# Portions adapted from HiQS-Labs/Needle-fork at f7c7047, Apache-2.0.
# Attribution and modification notice: ../NOTICE; license: ../licenses/Apache-2.0.txt.
"""Known-truth scoring and explicit confidence gates."""
import json
from pathlib import Path
from .answers import number

BUCKETS = (("<0.5", 0, 0.5), ("0.5-0.8", 0.5, 0.8), (">=0.8", 0.8, 1.01))


def hit_equal(truth, pred):
    return truth == pred


def within(tolerance):
    """Score hit: prediction within `tolerance` rubric levels of the labelled level."""
    return lambda truth, pred: abs(pred - truth) <= tolerance


def above(threshold):
    """Noul hit: the thresholded probability agrees with the boolean label."""
    return lambda truth, pred: (pred >= threshold) == truth


def aligned(truth, pred, conf=None):
    if not truth or len(truth) != len(pred) or (conf is not None and len(conf) != len(truth)):
        raise ValueError("inputs must be nonempty and aligned")
    if conf is not None:
        for value in conf:
            number(value, unit=True)


def metrics(truth, pred, classes):
    aligned(truth, pred)
    pairs = [(t, p) for t, p in zip(truth, pred) if t is not None]
    universe = sorted(set(classes) | {t for t, _ in pairs})
    index = {label: i for i, label in enumerate(universe)}
    confusion = [[0] * len(universe) for _ in universe]
    for t, p in pairs:
        if p not in index:
            raise ValueError("prediction outside classes union truth")
        confusion[index[t]][index[p]] += 1
    scores = []
    for label in universe:
        tp = sum(t == p == label for t, p in pairs)
        fp = sum(t != label and p == label for t, p in pairs)
        fn = sum(t == label and p != label for t, p in pairs)
        scores.append(2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else 0.0)
    correct = sum(t == p for t, p in pairs)
    return {"labeled_n": len(pairs), "uncertain_truth_n": len(truth) - len(pairs),
            "correct": correct, "raw_accuracy": correct / len(pairs) if pairs else 0.0,
            "macro_f1": sum(scores) / len(scores) if scores else 0.0,
            "confusion_labels": universe, "confusion": confusion}


def score_metrics(truth, pred, tolerance):
    aligned(truth, pred)
    tolerance = number(tolerance)
    if tolerance < 0:
        raise ValueError("tolerance must be nonnegative")
    pairs = [(number(t), number(p)) for t, p in zip(truth, pred) if t is not None]
    correct = sum(abs(p - t) <= tolerance for t, p in pairs)
    return {"labeled_n": len(pairs), "uncertain_truth_n": len(truth) - len(pairs),
            "correct": correct, "raw_accuracy": correct / len(pairs) if pairs else 0.0,
            "mae": sum(abs(p - t) for t, p in pairs) / len(pairs) if pairs else 0.0, "tolerance": tolerance}


def noul_metrics(truth, pred, threshold):
    aligned(truth, pred)
    threshold = number(threshold, unit=True)
    if any(t is not None and type(t) is not bool for t in truth):
        raise ValueError("noul truth must be boolean or null")
    pairs = [(t, number(p, unit=True)) for t, p in zip(truth, pred) if t is not None]
    correct = sum((p >= threshold) == t for t, p in pairs)
    return {"labeled_n": len(pairs), "uncertain_truth_n": len(truth) - len(pairs),
            "correct": correct, "raw_accuracy": correct / len(pairs) if pairs else 0.0,
            "brier": sum((p - t) ** 2 for t, p in pairs) / len(pairs) if pairs else 0.0, "threshold": threshold}


def confidence_table(truth, pred, conf, hit=hit_equal):
    aligned(truth, pred, conf)
    rows = []
    for name, lo, hi in BUCKETS:
        members = [i for i, c in enumerate(conf) if lo <= c < hi and truth[i] is not None]
        hits = sum(hit(truth[i], pred[i]) for i in members)
        rows.append({"bucket": name, "n": len(members), "correct": hits,
                     "accuracy": hits / len(members) if members else 0.0})
    return rows


def gate(truth, pred, conf, floor=0.8, min_accuracy=0.9, min_coverage=0.6, hit=hit_equal):
    aligned(truth, pred, conf)
    for value in (floor, min_accuracy, min_coverage):
        number(value, unit=True)
    scored = [i for i, t in enumerate(truth) if t is not None]
    high = [i for i in scored if conf[i] >= floor]
    hits = sum(hit(truth[i], pred[i]) for i in high)
    accuracy = hits / len(high) if high else 0.0
    coverage = len(high) / len(scored) if scored else 0.0
    return {"scored_rows": len(scored), "high_confidence_rows": len(high),
            "high_confidence_correct": hits, "accuracy": accuracy, "coverage": coverage,
            "met": bool(high) and accuracy >= min_accuracy and coverage >= min_coverage,
            "confidence_floor": floor, "min_accuracy": min_accuracy, "min_coverage": min_coverage}


def agreement(pred, annotator):
    """ID -> label mappings, or a JSON file containing that annotator mapping."""
    if isinstance(annotator, (str, Path)):
        annotator = json.loads(Path(annotator).read_text())
    if not pred or set(pred) != set(annotator):
        raise ValueError("annotator IDs must exactly match predictions")
    hits = sum(value == annotator[key] for key, value in pred.items())
    return {"n": len(pred), "correct": hits, "agreement": hits / len(pred)}


def fn_zero_threshold(truth, fail_probabilities):
    """Exploratory in-sample fit: predict fail when P(fail) >= threshold.

    Highest observed threshold with zero false negatives; ties predict fail.
    Not a held-out gate or an assertion about future false negatives.
    """
    aligned(truth, fail_probabilities, fail_probabilities)
    if any(t not in ("pass", "fail") for t in truth) or "fail" not in truth:
        raise ValueError("binary labels and at least one failure are required")
    threshold = min(p for t, p in zip(truth, fail_probabilities) if t == "fail")
    return {"threshold": threshold, "false_negatives": 0,
            "false_positives": sum(t == "pass" and p >= threshold for t, p in zip(truth, fail_probabilities)),
            "failure_support": truth.count("fail"), "in_sample_only": True}


def metrics_from_confusion(confusion, classes, uncertain_truth_n=0):
    """Replay aggregate counts without inventing record-level truth assignments."""
    if len(confusion) != len(classes) or len(set(classes)) != len(classes):
        raise ValueError("confusion shape mismatch")
    truth, pred = [], []
    for i, row in enumerate(confusion):
        if len(row) != len(classes):
            raise ValueError("confusion shape mismatch")
        for j, count in enumerate(row):
            if type(count) is not int or count < 0:
                raise ValueError("invalid confusion count")
            truth.extend([classes[i]] * count)
            pred.extend([classes[j]] * count)
    result = metrics(truth, pred, classes)
    if type(uncertain_truth_n) is not int or uncertain_truth_n < 0:
        raise ValueError("invalid uncertain count")
    result["uncertain_truth_n"] = uncertain_truth_n
    return result


def binary_counts(truth, pred):
    aligned(truth, pred)
    if any(t not in ("pass", "fail") for t in truth + pred):
        raise ValueError("pass/fail labels required")
    fn = sum(t == "fail" and p == "pass" for t, p in zip(truth, pred))
    return {"false_negatives": fn,
            "false_positives": sum(t == "pass" and p == "fail" for t, p in zip(truth, pred)),
            "failure_support": truth.count("fail"), "fn_floor_met": "fail" in truth and fn == 0}
