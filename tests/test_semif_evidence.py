import copy
import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "evidence" / "2026-09-22-semif-six-action" / "semif_next_action.py"
SPEC = importlib.util.spec_from_file_location("semif_next_action", SCRIPT)
semif = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(semif)


class SemIfEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.sentinel = "GH22-PRIVATE-STATE-SENTINEL-7f53"
        self.holdout = self.root / "holdout.jsonl"
        rows = []
        for index, label in enumerate(semif.LABELS):
            rows.append({
                "query": "{} row {}".format(self.sentinel, index),
                "answers": [{"name": label}],
            })
        self._write_jsonl(self.holdout, rows)
        self.holdout_sha = semif.sha256_file(self.holdout)
        self.support = {label: 1 for label in semif.LABELS}
        self.baselines = self.root / "baselines.json"
        self._write_baselines()
        self.semif_input = self.root / "semif-input.jsonl"
        semif.prepare(self.holdout, self.baselines, self.semif_input,
                      expected_sha=self.holdout_sha, expected_rows=6,
                      expected_support=self.support)

    def tearDown(self):
        self.temp.cleanup()

    @staticmethod
    def _write_jsonl(path, rows):
        path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
                        encoding="utf-8")

    def _write_baselines(self, phase_backoff=42):
        report = {
            "train_rows": 500,
            "holdout_rows": 100,
            "metrics": {
                "majority": {"correct": 26, "accuracy_pct": 26.0},
                "repeat_last": {"correct": 22, "accuracy_pct": 22.0},
                "markov_1": {"correct": 37, "accuracy_pct": 37.0},
                "phase_backoff": {"correct": phase_backoff,
                                  "accuracy_pct": float(phase_backoff)},
            },
            "inputs": {"train_sha256": semif.TRAIN_SHA256,
                       "holdout_sha256": self.holdout_sha},
        }
        self.baselines.write_text(json.dumps(report), encoding="utf-8")

    @staticmethod
    def _model():
        commit = semif.MLX_LM_COMMIT
        return {
            "source": semif.MODEL_SOURCE,
            "revision": semif.MODEL_REVISION,
            "backend": "mlx",
            "mlx_version": "0.32.2",
            "mlx_lm_version": "0.32.0",
            "transformers_version": "5.17.0",
            "mlx_lm_source": {
                "url": "https://github.com/ml-explore/mlx-lm.git",
                "vcs_info": {"vcs": "git", "commit_id": commit,
                             "requested_revision": commit},
            },
            "allocator_cache_limit_bytes": 268435456,
            "dtype": list(semif.DTYPES),
            "quantization": None,
            "source_artifact_sha256": {
                "model.safetensors": hashlib.sha256(b"model").hexdigest(),
                "config.json": hashlib.sha256(b"config").hexdigest(),
            },
            "serving_config": "mlx-direct-v1",
        }

    def _raw_rows(self):
        holdout = semif.read_jsonl(self.holdout)
        rows = []
        for index, source in enumerate(holdout):
            gold = source["answers"][0]["name"]
            probabilities = [0.06] * len(semif.LABELS)
            probabilities[semif.LABELS.index(gold)] = 0.70
            token = "row-{:03d}".format(index).encode()
            rows.append({
                "id": "row-{:03d}".format(index),
                "option_ids": list(semif.LABELS),
                "probabilities": probabilities,
                "option_logits": list(probabilities),
                "answer_token_ids": list(range(len(semif.LABELS))),
                "input_tokens": 100 + index,
                "input_ids_sha256": hashlib.sha256(b"ids" + token).hexdigest(),
                "prompt_sha256": hashlib.sha256(b"prompt" + token).hexdigest(),
                "prompt_version": "direct-options-v1",
                "model": self._model(),
                "readout": semif.READOUT,
                "probability_status": semif.PROBABILITY_STATUS,
                "forward_seconds": 0.1 + index / 100,
                "total_seconds": 0.2 + index / 100,
            })
        return rows

    def _summarize(self, raw_rows, stem):
        raw = self.root / (stem + "-raw.jsonl")
        results = self.root / (stem + "-results.json")
        provenance = self.root / (stem + "-provenance.json")
        self._write_jsonl(raw, raw_rows)
        value = semif.summarize(
            self.holdout, self.baselines, self.semif_input, raw, results, provenance,
            "a" * 40, expected_sha=self.holdout_sha, expected_rows=6,
            expected_support=self.support)
        return value, results, provenance

    def test_green_projection_metrics_and_sentinel_absence(self):
        (result, _), results, provenance = self._summarize(self._raw_rows(), "green")
        verification = self.root / "verification.json"
        checked = semif.verify(results, provenance, verification)
        self.assertEqual(result["metrics"]["correct"], 6)
        self.assertEqual(checked["metrics"], result["metrics"])
        for path in (results, provenance, verification):
            self.assertNotIn(self.sentinel, path.read_text(encoding="utf-8"))
        self.assertEqual(set(result["predictions"][0]), semif.PREDICTION_FIELDS)

    def test_holdout_and_all_four_baselines_are_frozen(self):
        with self.assertRaisesRegex(ValueError, "holdout hash mismatch"):
            semif.load_holdout(self.holdout, expected_sha="0" * 64,
                               expected_rows=6, expected_support=self.support)
        self._write_baselines(phase_backoff=41)
        with self.assertRaisesRegex(ValueError, "baseline metric mismatch"):
            semif.validate_baselines(self.baselines, holdout_sha=self.holdout_sha)

    def test_raw_schema_model_revision_and_quantization_fail_closed(self):
        cases = []
        extra = self._raw_rows()
        extra[0]["note"] = self.sentinel
        cases.append(("extra", extra, "unexpected raw SemIf field"))
        revision = self._raw_rows()
        revision[0]["model"]["revision"] = "0" * 40
        cases.append(("revision", revision, "model identity or source precision mismatch"))
        quantized = self._raw_rows()
        quantized[0]["model"]["quantization"] = {"bits": 4, "group_size": 64, "mode": "affine"}
        cases.append(("quantized", quantized, "model identity or source precision mismatch"))
        for stem, rows, message in cases:
            with self.subTest(stem=stem):
                with self.assertRaisesRegex(ValueError, message):
                    self._summarize(rows, stem)
                self.assertFalse((self.root / (stem + "-results.json")).exists())

    def test_missing_duplicate_and_option_drift_fail_closed(self):
        missing = self._raw_rows()[:-1]
        duplicate = self._raw_rows()
        duplicate[1]["id"] = duplicate[0]["id"]
        options = self._raw_rows()
        options[0]["option_ids"][0] = "other"
        cases = (("missing", missing, "row-count mismatch"),
                 ("duplicate", duplicate, "raw ID or option order mismatch"),
                 ("options", options, "raw ID or option order mismatch"))
        for stem, rows, message in cases:
            with self.subTest(stem=stem):
                with self.assertRaisesRegex(ValueError, message):
                    self._summarize(rows, stem)

    def test_independent_verifier_rejects_tampered_metrics(self):
        (_, _), results, provenance = self._summarize(self._raw_rows(), "tamper")
        value = json.loads(results.read_text(encoding="utf-8"))
        value["metrics"]["correct"] = 0
        results.write_text(json.dumps(value), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "independent metrics mismatch"):
            semif.verify(results, provenance, self.root / "never.json")


if __name__ == "__main__":
    unittest.main()
