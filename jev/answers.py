"""Typed accessors; absent retained fields are never fabricated."""
import math

MODEL = "jev-1.13.0"


def number(value, unit=False):
    if type(value) not in (int, float) or not math.isfinite(value):
        raise ValueError("expected a finite number")
    if unit and not 0 <= value <= 1:
        raise ValueError("expected a number in [0, 1]")
    return float(value)


class Answer:
    def __init__(self, response, request_sha256, response_sha256):
        if not isinstance(response, dict) or response.get("model") != MODEL:
            raise ValueError("response must identify the pinned model")
        if not isinstance(response.get("answers"), dict) or not response["answers"]:
            raise ValueError("response has no answers")
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
