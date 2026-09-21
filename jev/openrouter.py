# Transport adapted from jev/client.py (Needle-fork f7c7047, Apache-2.0).
# See ../NOTICE and ../licenses/Apache-2.0.txt.
"""Pinned OpenRouter Decisions adapter; no chat-completions fallback."""
import json
import math
import os
import time
import urllib.error
import urllib.request
from email.utils import parsedate_to_datetime
from pathlib import Path

from .answers import Answer, number
from .client import MockClient, _NoRedirect, canonical, request_bytes as direct_request_bytes, sha256

MODEL = "typesafe/jev-1.13"
RESPONSE_MODEL = "typesafe/jev-1.13-20260917"
ENDPOINT = "https://openrouter.ai/api/alpha/decisions"


def load_key(key_file=None):
    key = Path(key_file).read_text().strip() if key_file else os.environ.get("OPENROUTER_API_KEY", "").strip()
    if not key:
        raise ValueError("no API key: set OPENROUTER_API_KEY or use --key-file")
    return key


def request_bytes(state, questions):
    payload = json.loads(direct_request_bytes(state, questions))
    payload["model"] = MODEL
    return canonical(payload)


class OpenRouterAnswer(Answer):
    expected_model = RESPONSE_MODEL


class OpenRouterClient:
    def __init__(self, key, model=MODEL, endpoint=ENDPOINT):
        if model != MODEL or endpoint != ENDPOINT:
            raise ValueError("only the pinned OpenRouter Decisions route is allowed")
        if not isinstance(key, str) or not key.strip():
            raise ValueError("no API key")
        self._key, self.endpoint = key.strip(), endpoint
        self.input_tokens, self.output_tokens, self.cost = 0, 0, 0.0
        self.models_seen = set()

    def _answer(self, raw_request, raw_response, questions):
        parsed = json.loads(raw_response)
        answer = OpenRouterAnswer(parsed, sha256(raw_request), sha256(raw_response))
        if parsed.get("provider") != "TypeSafe":
            raise ValueError("unexpected OpenRouter provider")
        if set(parsed["answers"]) != set(questions):
            raise ValueError("answer/question coverage mismatch")
        for name, question in questions.items():
            kind = question["type"]
            value = getattr(answer, kind)(name)
            if kind == "choice" and value not in question["criteria"]:
                raise ValueError("choice outside criteria")
            if kind == "score" and not 0 <= value <= len(question["criteria"]) - 1:
                raise ValueError("score outside rubric range")
            if kind in ("choice", "score"):
                answer.confidence(name)
        usage = parsed.get("usage")
        if not isinstance(usage, dict):
            raise ValueError("usage must be an object")
        for field in ("input_tokens", "output_tokens"):
            if type(usage.get(field)) is not int or usage[field] < 0:
                raise ValueError("invalid token usage")
        cost = number(usage.get("cost"))
        if cost < 0 or not math.isfinite(self.cost + cost):
            raise ValueError("invalid cost")
        self.input_tokens += usage["input_tokens"]
        self.output_tokens += usage["output_tokens"]
        self.cost += cost
        self.models_seen.add(answer.model)
        return answer

    def ask(self, state, questions):
        if os.environ.get("CI"):
            raise ValueError("live requests are disabled in CI")
        raw = request_bytes(state, questions)
        req = urllib.request.Request(self.endpoint, data=raw, method="POST", headers={
            "Authorization": "Bearer " + self._key, "Content-Type": "application/json"})
        opener = urllib.request.build_opener(_NoRedirect)
        for attempt in range(3):
            try:
                with opener.open(req, timeout=60) as response:
                    data = response.read()
                return self._answer(raw, data, questions)
            except urllib.error.HTTPError as error:
                retry = error.code == 429 or 500 <= error.code <= 599
                after = error.headers.get("retry-after") if error.headers else None
                code = error.code
                error.close()
                if not retry or attempt == 2:
                    raise RuntimeError(f"Jev HTTP {code}") from None
                delay = 2 ** attempt
                if after:
                    try:
                        delay = float(after)
                    except ValueError:
                        try:
                            delay = parsedate_to_datetime(after).timestamp() - time.time()
                        except (ValueError, TypeError, OverflowError):
                            pass
                if not math.isfinite(delay) or delay > 60:
                    raise RuntimeError("Retry-After exceeds retry wait budget") from None
                time.sleep(max(0, delay))
            except (urllib.error.URLError, TimeoutError, OSError):
                raise RuntimeError("Jev transport failed") from None


class OpenRouterMockClient(OpenRouterClient):
    def __init__(self, responses):
        super().__init__("mock-only")
        self._responses = iter(responses)

    def ask(self, state, questions):
        raw = request_bytes(state, questions)
        try:
            response = next(self._responses)
        except StopIteration:
            raise ValueError("mock responses exhausted") from None
        return self._answer(raw, canonical(response), questions)

    finish = MockClient.finish
