import copy
import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "evidence" / "2026-09-22-laya-six-action" / "laya_next_action.py"
SPEC = importlib.util.spec_from_file_location("laya_next_action", SCRIPT)
laya = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(laya)


class FakeTokenizer:
    mask_token = "[MASK]"
    mask_token_id = 7

    def __init__(self, instruction_tokens=20, option_tokens=5):
        self.instruction_tokens = instruction_tokens
        self.option_tokens = option_tokens

    def __call__(self, text, add_special_tokens=False):
        count = self.instruction_tokens if text.startswith("choice question: ") else self.option_tokens
        return {"input_ids": list(range(count))}


class LayaEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.sentinel = "GH25-PRIVATE-STATE-SENTINEL-a91d"
        self.holdout = self.root / "holdout.jsonl"
        rows = []
        for index, label in enumerate(laya.LABELS):
            rows.append({"query": "{} row {}".format(self.sentinel, index),
                         "answers": [{"name": label}]})
        self._write_jsonl(self.holdout, rows)
        self.holdout_sha = laya.sha256_file(self.holdout)
        self.support = {label: 1 for label in laya.LABELS}
        self.baselines = self.root / "baselines.json"
        self._write_baselines()
        self.laya_input = self.root / "laya-input.jsonl"
        laya.prepare(
            self.holdout, self.baselines, self.laya_input,
            expected_sha=self.holdout_sha, expected_rows=6,
            expected_support=self.support, expected_baselines_sha=None,
        )

    def tearDown(self):
        self.temp.cleanup()

    @staticmethod
    def _write_jsonl(path, rows):
        path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows),
                        encoding="utf-8")

    def _write_baselines(self, phase_backoff=42):
        report = {
            "train_rows": 500, "holdout_rows": 100,
            "metrics": {
                "majority": {"correct": 26, "accuracy_pct": 26.0},
                "repeat_last": {"correct": 22, "accuracy_pct": 22.0},
                "markov_1": {"correct": 37, "accuracy_pct": 37.0},
                "phase_backoff": {"correct": phase_backoff,
                                  "accuracy_pct": float(phase_backoff)},
            },
            "inputs": {"train_sha256": laya.TRAIN_SHA256,
                       "holdout_sha256": self.holdout_sha},
        }
        self.baselines.write_text(json.dumps(report), encoding="utf-8")

    @staticmethod
    def _model():
        return {
            "source": laya.MODEL_SOURCE, "revision": laya.MODEL_REVISION,
            "laya_commit": laya.LAYA_COMMIT, **laya.MODEL_VERSIONS,
            "device": "cpu", "dtype": "torch.float32",
            "config_sha256": laya.MODEL_ARTIFACT_SHA256["rl_agent_config.json"],
            "source_artifact_sha256": dict(laya.MODEL_ARTIFACT_SHA256),
        }

    @staticmethod
    def _input_tokens(instruction=20, option=5, state=10):
        return 1 + instruction + 1 + 6 * (1 + option) + 1 + state + 1

    def _raw_rows(self):
        rows = []
        for index, label in enumerate(laya.LABELS):
            probabilities = [0.06] * len(laya.LABELS)
            probabilities[laya.LABELS.index(label)] = 0.70
            state_sha = hashlib.sha256(
                "{} row {}".format(self.sentinel, index).encode()).hexdigest()
            rows.append({
                "id": "row-{:03d}".format(index), "option_ids": list(laya.LABELS),
                "choice": label, "probabilities": probabilities, "confidence": 0.5,
                "max_option_probability": 0.70,
                "input_tokens": self._input_tokens(),
                "instruction_tokens_full": 20, "instruction_tokens_used": 20,
                "option_tokens_full": [5] * 6, "option_tokens_used": [5] * 6,
                "state_tokens_full": 10, "state_tokens_used": 10,
                "state_truncated": False, "state_sha256": state_sha,
                "request_sha256": laya._request_sha("row-{:03d}".format(index), state_sha),
                "route_model": "english", "elapsed_seconds": 0.1 + index / 100,
                "model": self._model(),
            })
        return rows

    def _summarize(self, raw_rows, stem):
        raw = self.root / (stem + "-raw.jsonl")
        results = self.root / (stem + "-results.json")
        provenance = self.root / (stem + "-provenance.json")
        self._write_jsonl(raw, raw_rows)
        value = laya.summarize(
            self.holdout, self.baselines, self.laya_input, raw, results, provenance,
            "a" * 40, expected_sha=self.holdout_sha, expected_rows=6,
            expected_support=self.support, expected_baselines_sha=None,
        )
        return value, raw, results, provenance

    def _verify(self, raw, results, provenance, output):
        return laya.verify(
            self.holdout, self.baselines, self.laya_input, raw, results, provenance, output,
            expected_sha=self.holdout_sha, expected_rows=6,
            expected_support=self.support, expected_baselines_sha=None,
        )

    def test_green_projection_verification_and_text_absence(self):
        (result, _), raw, results, provenance = self._summarize(self._raw_rows(), "green")
        verification = self.root / "verification.json"
        checked = self._verify(raw, results, provenance, verification)
        self.assertEqual(result["metrics"]["correct"], 6)
        self.assertEqual(checked["metrics"], result["metrics"])
        self.assertEqual(result["prediction_counts"], {label: 1 for label in laya.LABELS})
        for path in (results, provenance, verification):
            self.assertNotIn(self.sentinel, path.read_text(encoding="utf-8"))

    def test_holdout_and_all_four_baselines_are_frozen(self):
        with self.assertRaisesRegex(ValueError, "holdout hash mismatch"):
            laya.load_holdout(self.holdout, expected_sha="0" * 64,
                              expected_rows=6, expected_support=self.support)
        self._write_baselines(phase_backoff=41)
        with self.assertRaisesRegex(ValueError, "baseline metric mismatch"):
            laya.validate_baselines(self.baselines, holdout_sha=self.holdout_sha,
                                    expected_sha=None)

    def test_head_tokenization_rejects_instruction_or_option_loss(self):
        head = laya._head_tokenization(FakeTokenizer())
        self.assertFalse(head["truncated"])
        with self.assertRaisesRegex(ValueError, "instruction or option text is truncated"):
            laya._head_tokenization(FakeTokenizer(instruction_tokens=300))
        with self.assertRaisesRegex(ValueError, "instruction or option text is truncated"):
            laya._head_tokenization(FakeTokenizer(option_tokens=60))

    def test_raw_schema_model_and_probability_relations_fail_closed(self):
        cases = []
        extra = self._raw_rows()
        extra[0]["note"] = self.sentinel
        cases.append(("extra", extra, "unexpected raw Laya field"))
        version = self._raw_rows()
        version[0]["model"]["laya_version"] = "0.0.0"
        cases.append(("version", version, "model identity mismatch"))
        drift = self._raw_rows()
        drift[0]["probabilities"] = [0.1] * 6
        drift[0]["max_option_probability"] = 0.1
        cases.append(("sum", drift, "rounded-sum tolerance"))
        choice = self._raw_rows()
        choice[0]["choice"] = "other"
        cases.append(("choice", choice, "choice outside frozen labels"))
        maximum = self._raw_rows()
        maximum[0]["max_option_probability"] = 0.69
        cases.append(("maximum", maximum, "choice or maximum"))
        for stem, rows, message in cases:
            with self.subTest(stem=stem):
                with self.assertRaisesRegex(ValueError, message):
                    self._summarize(rows, stem)
                self.assertFalse((self.root / (stem + "-results.json")).exists())
                self.assertFalse((self.root / (stem + "-provenance.json")).exists())

    def test_probability_rounding_edge_and_native_tie_choice_are_valid(self):
        rows = self._raw_rows()
        rows[0]["probabilities"] = [0.1667] * 6
        rows[0]["choice"] = "search"
        rows[0]["max_option_probability"] = 0.1667
        (result, _), _, _, _ = self._summarize(rows, "rounding")
        self.assertEqual(result["predictions"][0]["choice"], "search")

    def test_verifier_reprojects_raw_route_head_choice_and_probability(self):
        (_, _), raw, results, provenance = self._summarize(self._raw_rows(), "canonical")
        originals = self._raw_rows()
        cases = []
        route = copy.deepcopy(originals)
        route[0]["route_model"] = "multilingual"
        cases.append(("route", route))
        head = copy.deepcopy(originals)
        head[0]["instruction_tokens_used"] = 19
        head[0]["input_tokens"] -= 1
        cases.append(("head", head))
        choice = copy.deepcopy(originals)
        choice[0]["choice"] = "git"
        cases.append(("choice", choice))
        probability = copy.deepcopy(originals)
        probability[0]["probabilities"] = [0.07, 0.05, 0.06, 0.06, 0.06, 0.70]
        probability[0]["choice"] = "search"
        cases.append(("probability", probability))
        for stem, rows in cases:
            mutated = self.root / (stem + "-mutated.jsonl")
            output = self.root / (stem + "-verification.json")
            self._write_jsonl(mutated, rows)
            with self.subTest(stem=stem):
                with self.assertRaises(ValueError):
                    self._verify(mutated, results, provenance, output)
                self.assertFalse(output.exists())
        self.assertTrue(raw.exists())

    def test_verifier_rejects_committed_schema_and_binding_drift(self):
        (_, _), raw, results, provenance = self._summarize(self._raw_rows(), "binding")
        result_value = json.loads(results.read_text(encoding="utf-8"))
        result_value["extra"] = True
        results.write_text(json.dumps(result_value), encoding="utf-8")
        output = self.root / "never.json"
        with self.assertRaisesRegex(ValueError, "results schema drift"):
            self._verify(raw, results, provenance, output)
        self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
