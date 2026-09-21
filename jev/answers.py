"""Typed accessors; absent retained fields are never fabricated."""
import math
import os
import re


def pinned_model(value):
    # Exact versions only: an alias such as jev-latest moves, so results under it are not reproducible.
    if not isinstance(value, str) or not re.fullmatch(r"jev-\d+\.\d+\.\d+", value):
        raise ValueError("model must be an exact pinned version")
    return value


MODEL = pinned_model(os.environ.get("JEV_MODEL", "jev-1.13.0"))  # JEV_MODEL is the operator's shadow-run override.


def number(value, unit=False):
    if type(value) not in (int, float) or not math.isfinite(value):
        raise ValueError("expected a finite number")
    if unit and not 0 <= value <= 1:
        raise ValueError("expected a number in [0, 1]")
    return float(value)


class Answer:
    expected_model = MODEL

    def __init__(self, response, request_sha256, response_sha256):
        if not isinstance(response, dict) or response.get("model") != self.expected_model:
            raise ValueError("response must identify the pinned model")
        if not isinstance(response.get("answers"), dict) or not response["answers"]:
            raise ValueError("response has no answers")
        if any(not isinstance(item, dict) for item in response["answers"].values()):
            raise ValueError("each answer must be an object")
        self.response = response
        self.model = response["model"]
        self.request_sha256 = request_sha256
        self.response_sha256 = response_sha256

    def _typed(self, name, kind):
        answer = self.response["answers"][name]
        if answer.get("type") != kind:
            raise ValueError("answer type mismatch")
        return answer

    def choice(self, name) -> str:
        value = self._typed(name, "choice")["choice"]
        if not isinstance(value, str) or not value:
            raise ValueError("choice must be a nonempty string")
        return value

    def score(self, name) -> float:
        return number(self._typed(name, "score")["score"])

    def noul(self, name) -> float:
        return number(self._typed(name, "noul")["noul"], unit=True)

    def confidence(self, name) -> float:
        item = self.response["answers"][name]
        if item["type"] not in ("choice", "score"):
            raise ValueError("Noul has no separate confidence")
        return number(item["confidence"], unit=True)

    def project(self, questions) -> dict:
        """Typed fields only; never state, arbitrary API extensions, or error text."""
        values = {}
        for name, question in questions.items():
            kind = question["type"]
            values[name] = {"type": kind, kind: getattr(self, kind)(name)}
            if kind in ("choice", "score"):
                values[name]["confidence"] = self.confidence(name)
                if "probabilities" in self.response["answers"][name]:
                    try:
                        values[name]["probabilities"] = self.probabilities(name)
                    except (ValueError, KeyError, TypeError):
                        # Probabilities are optional for scoring. Keep the typed verdict
                        # and disclose the rejected distribution without inventing one.
                        values[name]["probabilities_status"] = "invalid"
        return values

    def probabilities(self, name) -> dict:
        item = self.response["answers"][name]
        if item["type"] not in ("choice", "score"):
            raise ValueError("Noul has no probability distribution")
        values = item["probabilities"]  # missing in reconstructed historical mocks
        if not isinstance(values, dict) or not values:
            raise ValueError("expected probability map")
        result = {k: number(v, unit=True) for k, v in values.items()}
        if not math.isclose(sum(result.values()), 1, abs_tol=1e-6):
            raise ValueError("probabilities must sum to one")
        return result
