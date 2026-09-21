# Portions adapted from HiQS-Labs/Needle-fork at f7c7047, Apache-2.0.
# Attribution and modification notice: ../NOTICE; license: ../licenses/Apache-2.0.txt.
"""Canonical requests, byte hashes, bounded retries, and ordered offline replay."""
import hashlib
import json
import math
import os
import time
import urllib.error
import urllib.request
from email.utils import parsedate_to_datetime
from pathlib import Path

from .answers import Answer, MODEL

ENDPOINT = "https://api.typesafe.ai/v1/systemone"


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def sha256(raw):
    return hashlib.sha256(raw).hexdigest()


def load_key(key_file=None):
    key = Path(key_file).read_text().strip() if key_file else os.environ.get("TYPESAFE_API_KEY", "").strip()
    if not key:
        raise ValueError("no API key: set TYPESAFE_API_KEY or use --key-file")
    return key


def validate_questions(questions):
    """Provider contract: Choice criteria map labels to glosses, Score criteria list ordered levels, Noul has none."""
    if not isinstance(questions, dict) or not questions:
        raise ValueError("questions must be nonempty")
    for name, question in questions.items():
        if not isinstance(name, str) or not name or not isinstance(question, dict):
            raise ValueError("question names and bodies must be nonempty")
        kind, criteria = question.get("type"), question.get("criteria")
        if kind not in ("choice", "score", "noul") or not isinstance(question.get("instructions"), str) or not question["instructions"].strip():
            raise ValueError("question needs a supported type and instructions")
        if kind == "choice":
            if not isinstance(criteria, dict) or not criteria or any(
                    not isinstance(k, str) or not k.strip() or not isinstance(v, str) or not v.strip() for k, v in criteria.items()):
                raise ValueError("choice criteria must map nonempty labels to nonempty glosses")
        elif kind == "score":
            if not isinstance(criteria, list) or len(criteria) < 2 or any(not isinstance(c, str) or not c.strip() for c in criteria):
                raise ValueError("score criteria must be an ordered list of at least two level descriptions")
        elif "criteria" in question:
            raise ValueError("noul questions take instructions only")
    return questions


def request_bytes(state, questions):
    if not isinstance(state, (str, dict, list)) or not state or (isinstance(state, str) and not state.strip()):
        raise ValueError("state must be nonempty")
    validate_questions(questions)
    return canonical({"state": state, "model": MODEL, "questions": questions})


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError("API redirect refused")


class JevClient:
    def __init__(self, key, model=MODEL, endpoint=ENDPOINT):
        if model != MODEL:
            raise ValueError("only the pinned model is allowed")
        if not isinstance(key, str) or not key.strip():
            raise ValueError("no API key")
        if endpoint != ENDPOINT:
            raise ValueError("only the TypeSafe endpoint is allowed")
        self._key, self.endpoint = key.strip(), endpoint
        self.input_tokens, self.models_seen = 0, set()

    def _answer(self, raw_request, raw_response, questions):
        parsed = json.loads(raw_response)
        answer = Answer(parsed, sha256(raw_request), sha256(raw_response))
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
        usage = parsed.get("usage", {})
        if not isinstance(usage, dict):
            raise ValueError("usage must be an object")
        tokens = usage.get("input_tokens", 0)
        if type(tokens) is not int or tokens < 0:
            raise ValueError("invalid token usage")
        self.input_tokens += tokens
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


class MockClient(JevClient):
    def __init__(self, responses):
        self._responses = iter(responses)
        self.input_tokens, self.models_seen = 0, set()

    def ask(self, state, questions):
        raw = request_bytes(state, questions)
        try:
            response = next(self._responses)
        except StopIteration:
            raise ValueError("mock responses exhausted") from None
        return self._answer(raw, canonical(response), questions)

    def finish(self):
        exhausted = object()
        if next(self._responses, exhausted) is not exhausted:
            raise ValueError("unused mock responses")
