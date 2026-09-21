"""Deterministic first-match policy over typed answers. The policy is data, so it hashes and freezes like a question set."""
from .answers import number
from .client import canonical, sha256

LEAF_KEYS = ("choice", "min", "max", "min_confidence")


def _validate_condition(cond):
    if not isinstance(cond, dict):
        raise ValueError("condition must be an object")
    if "any" in cond or "all" in cond:
        branches = cond.get("any", cond.get("all"))
        if len(cond) != 1 or not isinstance(branches, list) or not branches:
            raise ValueError("any/all must be the only key and list at least one condition")
        for child in branches:
            _validate_condition(child)
    elif "rule" in cond:
        if len(cond) != 1 or not isinstance(cond["rule"], str) or not cond["rule"]:
            raise ValueError("rule condition names one nonempty rule")
    else:
        if not isinstance(cond.get("axis"), str) or not cond["axis"] or not any(k in cond for k in LEAF_KEYS) \
                or set(cond) - {"axis", *LEAF_KEYS}:
            raise ValueError("axis condition needs an axis and at least one of choice/min/max/min_confidence")
        for key in ("min", "max"):
            if key in cond:
                number(cond[key])
        if "min_confidence" in cond:
            number(cond["min_confidence"], unit=True)
        if "choice" in cond and (not isinstance(cond["choice"], str) or not cond["choice"]):
            raise ValueError("choice condition must be a nonempty label")


def validate_policy(policy):
    if not isinstance(policy, dict) or not isinstance(policy.get("default"), str) or not policy["default"] \
            or not isinstance(policy.get("clauses"), list):
        raise ValueError("policy needs a default decision and a clauses list")
    for clause in policy["clauses"]:
        if not isinstance(clause, dict) or not isinstance(clause.get("decision"), str) or not clause["decision"] \
                or ("any" in clause) == ("all" in clause):
            raise ValueError("clause needs a decision and exactly one of any/all")
        _validate_condition({k: v for k, v in clause.items() if k != "decision"})
    return policy


def _holds(cond, answers, rule_hits):
    if "any" in cond:
        return any(_holds(child, answers, rule_hits) for child in cond["any"])
    if "all" in cond:
        return all(_holds(child, answers, rule_hits) for child in cond["all"])
    if "rule" in cond:
        return cond["rule"] in rule_hits
    answer = answers.get(cond["axis"])
    if not isinstance(answer, dict):
        return False  # Unknown axis or malformed projection never satisfies a condition.
    kind = answer.get("type")
    if kind not in ("choice", "score", "noul") or kind not in answer:
        return False
    value = answer[kind]
    try:
        if kind == "choice":
            if not isinstance(value, str) or not value:
                return False
        elif kind in ("score", "noul"):
            value = number(value, unit=kind == "noul")
        else:
            return False
    except ValueError:
        return False
    checks = []
    if "choice" in cond:
        checks.append(value == cond["choice"])
    if "min" in cond:
        checks.append(kind in ("score", "noul") and value >= cond["min"])
    if "max" in cond:
        checks.append(kind in ("score", "noul") and value <= cond["max"])
    if "min_confidence" in cond:
        try:
            confidence = number(answer["confidence"], unit=True)
        except (KeyError, ValueError):
            return False
        checks.append(kind in ("choice", "score") and confidence >= cond["min_confidence"])
    return all(checks)


def decide(policy, answers, rule_hits=()):
    """First clause whose condition holds wins; none → the policy's default (set it to the fail-closed value)."""
    validate_policy(policy)
    digest = sha256(canonical(policy))
    hits = set(rule_hits)
    for index, clause in enumerate(policy["clauses"]):
        if _holds({k: v for k, v in clause.items() if k != "decision"}, answers, hits):
            return {"decision": clause["decision"], "clause": index, "policy_sha256": digest}
    return {"decision": policy["default"], "clause": None, "policy_sha256": digest}
