import hashlib
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "spike/work_classification"))
import jev_zero_shot as jz


def test_text_template_matches_547():
    rec = {"repo": "HiQS-Labs/X", "title": "fix: thing", "description": "body"}
    assert jz.text_of(rec) == "Project: HiQS-Labs/X\nTitle: fix: thing\nDescription: body"


def test_metrics_counts_macro_f1_and_null_truth():
    # 3 labeled rows + 1 null-truth row; class "d" has zero support and zero predictions -> F1 0.
    truth = ["a", "b", "a", None, "c"]
    pred = ["a", "b", "b", "a", "c"]
    m = jz.metrics(truth, pred, ["a", "b", "c", "d"])
    assert m["labeled_n"] == 4 and m["uncertain_truth_n"] == 1 and m["correct"] == 3
    assert m["raw_accuracy"] == pytest.approx(0.75)
    # a: tp1 fn1 -> 2/3 ; b: tp1 fp1 -> 2/3 ; c: 1.0 ; d: 0 (zero_division=0)  => mean 0.5833
    assert m["macro_f1"] == pytest.approx((2 / 3 + 2 / 3 + 1.0 + 0.0) / 4)
    assert m["confusion_labels"] == ["a", "b", "c", "d"]
    assert m["confusion"][0] == [1, 1, 0, 0]


def test_metrics_matches_sklearn_when_available():
    sk = pytest.importorskip("sklearn.metrics")
    truth = ["a", "b", "a", "c", "b"]
    pred = ["a", "b", "b", "c", "a"]
    universe = ["a", "b", "c", "d"]
    ours = jz.macro_f1(truth, pred, universe)
    theirs = sk.f1_score(truth, pred, labels=universe, average="macro", zero_division=0)
    assert ours == pytest.approx(theirs)


def test_metrics_rejects_empty_and_misaligned():
    with pytest.raises(ValueError):
        jz.metrics([], [], ["a"])
    with pytest.raises(ValueError):
        jz.metrics(["a"], [], ["a"])


def test_confidence_table_ignores_null_truth():
    rows = jz.confidence_table(["a", None, "b"], ["a", "a", "a"], [0.9, 0.9, 0.2])
    by = {r["bucket"]: r for r in rows}
    assert by[">=0.8"] == {"bucket": ">=0.8", "n": 1, "correct": 1, "accuracy": 1.0}
    assert by["<0.5"] == {"bucket": "<0.5", "n": 1, "correct": 0, "accuracy": 0.0}


def test_freeze_check_aborts_on_mismatch(tmp_path):
    (tmp_path / "taxonomy.md").write_bytes(b"tampered")
    with pytest.raises(ValueError, match="freeze mismatch"):
        jz.verify_freeze(tmp_path, {"taxonomy.md": jz.FROZEN_HASHES["taxonomy.md"]})
    good = tmp_path / "ok.md"
    good.write_bytes(b"x")
    assert jz.verify_freeze(tmp_path, {"ok.md": hashlib.sha256(b"x").hexdigest()}) == {"ok.md": hashlib.sha256(b"x").hexdigest()}


def test_questions_are_forced_choice_over_taxonomy_classes():
    assert set(jz.CLASSES["purpose"]) == {"bug_fix", "feature_enhancement", "research_evaluation", "planning_design",
                                          "documentation", "maintenance", "testing_validation", "merge_closeout"}
    assert len(jz.CLASSES["area"]) == 12 and "none" not in jz.CLASSES["area"]
    body = jz.build_request({"repo": "r", "title": "t", "description": "d"})
    assert body["model"] == "jev-1.13.0" and set(body["questions"]) == {"purpose", "area"}
    json.dumps(body)  # serialisable


def test_repo_visibility_marks_errors_not_public():
    class P:
        def __init__(self, rc, out, err=""):
            self.returncode, self.stdout, self.stderr = rc, out, err

    def runner(cmd, capture_output, text):
        return P(0, "PUBLIC\n") if cmd[3] == "HiQS-Labs/pub" else P(1, "", "not found")

    vis = jz.repo_visibility(["HiQS-Labs/pub", "HiQS-Labs/priv", "HiQS-Labs/pub"], runner=runner)
    assert vis["HiQS-Labs/pub"] == "PUBLIC" and vis["HiQS-Labs/priv"].startswith("error:")
