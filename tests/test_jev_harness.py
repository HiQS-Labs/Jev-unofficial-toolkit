# Selected metric/control cases adapted from HiQS-Labs/Needle-fork f7c7047,
# Apache-2.0; see ../NOTICE and ../licenses/Apache-2.0.txt.
"""All tests are offline. Network and external commands fail closed by default."""
import contextlib
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError

from jev import openrouter
from jev.answers import Answer, MODEL
from jev.client import JevClient, MockClient, canonical, load_key, sha256
from jev.cli import main
from jev.eval import agreement, confidence_table, fn_zero_threshold, gate, metrics, metrics_from_confusion, binary_counts
from jev.guard import (commit, load_questions, repo_visibility, safe_results,
                       verify, verify_freeze, write_results)

ROOT = Path(__file__).resolve().parents[1]
Q = {"purpose": {"type": "choice", "instructions": "Choose a or b.", "criteria": {"a": "A", "b": "B"}}}


def response(choice="a", confidence=0.9):
    return {"model": MODEL, "usage": {"input_tokens": 7}, "answers": {
        "purpose": {"type": "choice", "choice": choice, "confidence": confidence,
                    "probabilities": {"a": 0.95, "b": 0.05}}}}


class HarnessTests(unittest.TestCase):
    def setUp(self):
        self.stack = contextlib.ExitStack()
        self.addCleanup(self.stack.close)
        for target in ("socket.socket.connect", "socket.create_connection", "urllib.request.urlopen",
                       "urllib.request.OpenerDirector.open", "subprocess.run", "subprocess.Popen"):
            self.stack.enter_context(patch(target, side_effect=AssertionError("network/process forbidden in tests")))
        self.tmp = Path(self.stack.enter_context(tempfile.TemporaryDirectory()))

    def router_response(self):
        value = response()
        value.update(model=openrouter.RESPONSE_MODEL, provider="TypeSafe", id="synthetic")
        value["usage"].update(output_tokens=0, cost=0.001)
        return value

    def test_openrouter_hashes_usage_and_typed_contract(self):
        canned = self.router_response()
        canned["answers"].update(rating={"type": "score", "score": 2, "confidence": 0.7},
                                 valid={"type": "noul", "noul": 0.8})
        questions = dict(Q, rating={"type": "score"}, valid={"type": "noul"})
        client = openrouter.OpenRouterMockClient([canned, canned])
        answer = client.ask("synthetic", questions)
        self.assertEqual(answer.request_sha256, sha256(canonical({
            "model": openrouter.MODEL, "state": "synthetic", "questions": questions})))
        self.assertEqual(answer.response_sha256, sha256(canonical(canned)))
        self.assertEqual(answer.choice("purpose"), "a")
        self.assertEqual(answer.score("rating"), 2)
        self.assertEqual(answer.noul("valid"), 0.8)
        self.assertEqual(answer.probabilities("purpose"), {"a": 0.95, "b": 0.05})
        with self.assertRaises(ValueError):
            openrouter.OpenRouterMockClient([canned]).finish()
        client.ask("synthetic", questions)
        client.finish()
        self.assertEqual((client.input_tokens, client.output_tokens, client.cost), (14, 0, 0.002))
        self.assertEqual(client.models_seen, {openrouter.RESPONSE_MODEL})
        with self.assertRaises(ValueError): client.ask("synthetic", questions)

    def test_openrouter_wrong_models_malformed_and_route_isolation(self):
        for model in (None, MODEL, openrouter.MODEL, "~typesafe/jev-latest",
                      "typesafe/jev-1.13-20990101"):
            canned = self.router_response(); canned["model"] = model
            with self.assertRaises(ValueError):
                openrouter.OpenRouterMockClient([canned]).ask("synthetic", Q)
        for field, value in (("answers", []), ("provider", "other"), ("usage", None)):
            canned = self.router_response(); canned[field] = value
            with self.assertRaises(ValueError):
                openrouter.OpenRouterMockClient([canned]).ask("synthetic", Q)
        for field, value in (("input_tokens", True), ("output_tokens", -1), ("cost", -1),
                             ("cost", "0.1"), ("cost", None)):
            canned = self.router_response(); canned["usage"][field] = value
            with self.assertRaises(ValueError):
                openrouter.OpenRouterMockClient([canned]).ask("synthetic", Q)
        for answers in ({}, {"purpose": []}, response("outside")["answers"]):
            canned = self.router_response(); canned["answers"] = answers
            with self.assertRaises(ValueError):
                openrouter.OpenRouterMockClient([canned]).ask("synthetic", Q)
        with self.assertRaises(ValueError): MockClient([self.router_response()]).ask("x", Q)
        with self.assertRaises(ValueError): openrouter.OpenRouterMockClient([response()]).ask("x", Q)
        for endpoint in ("https://api.typesafe.ai/v1/systemone", "https://openrouter.ai/api/v1/chat/completions"):
            with self.assertRaises(ValueError): openrouter.OpenRouterClient("test", endpoint=endpoint)
        with self.assertRaises(ValueError): openrouter.OpenRouterClient("test", model="~typesafe/jev-latest")
        with self.assertRaises(ValueError): JevClient("test", endpoint=openrouter.ENDPOINT)

    def test_openrouter_keys_and_ci(self):
        with patch.dict(os.environ, {"TYPESAFE_API_KEY": "direct-only"}, clear=True):
            with self.assertRaises(ValueError): openrouter.load_key()
        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "router-only"}, clear=True):
            self.assertEqual(openrouter.load_key(), "router-only")
            with self.assertRaises(ValueError): load_key()
        key = self.tmp / "router-key"; key.write_text("test-only\n")
        self.assertEqual(openrouter.load_key(key), "test-only")
        with self.assertRaises(ValueError): openrouter.OpenRouterClient(" ")
        with patch.dict(os.environ, {"CI": "true"}):
            with self.assertRaises(ValueError): openrouter.OpenRouterClient("test").ask("x", Q)
            openrouter.OpenRouterMockClient([self.router_response()]).ask("x", Q)

    def test_openrouter_canned_http_retries_and_exact_wire_hash(self):
        raw = json.dumps(self.router_response(), indent=2).encode()
        for code in (429, 500, 599):
            with patch.dict(os.environ, {}, clear=True), patch("time.sleep") as sleep, patch(
                    "urllib.request.OpenerDirector.open", side_effect=[
                        HTTPError("x", code, "secret", {"retry-after": "2"}, None), io.BytesIO(raw)]) as send:
                answer = openrouter.OpenRouterClient("router-only").ask("x", Q)
                req = send.call_args.args[0]
                self.assertEqual(req.full_url, openrouter.ENDPOINT)
                self.assertEqual(req.get_method(), "POST")
                self.assertEqual(req.get_header("Authorization"), "Bearer router-only")
                self.assertEqual(json.loads(req.data)["model"], openrouter.MODEL)
                self.assertEqual(answer.request_sha256, sha256(req.data))
                self.assertEqual(answer.response_sha256, sha256(raw))
                self.assertEqual(send.call_count, 2)
                sleep.assert_called_once_with(2)
        for code, count in ((401, 1), (503, 3)):
            with patch.dict(os.environ, {}, clear=True), patch("time.sleep"), patch(
                    "urllib.request.OpenerDirector.open", side_effect=HTTPError("x", code, "secret", {}, None)) as send:
                with self.assertRaisesRegex(RuntimeError, "^Jev HTTP " + str(code) + "$"):
                    openrouter.OpenRouterClient("test").ask("x", Q)
                self.assertEqual(send.call_count, count)
        for delay in ("61", "nan", "inf"):
            with patch.dict(os.environ, {}, clear=True), patch("time.sleep") as sleep, patch(
                    "urllib.request.OpenerDirector.open", side_effect=HTTPError("x", 429, "secret", {"retry-after": delay}, None)):
                with self.assertRaises(RuntimeError): openrouter.OpenRouterClient("test").ask("x", Q)
                sleep.assert_not_called()
        with self.assertRaises(ValueError):
            openrouter._NoRedirect().redirect_request(None, None, 302, "", {}, "https://example.com")

    def test_openrouter_cli_projection_manifest_and_fixture_isolation(self):
        state = self.tmp / "state.json"; state.write_text('"synthetic state never retained"')
        questions = load_questions("work_purpose_v3")
        canned = self.router_response()
        canned["answers"] = {axis: {"type": "choice", "choice": next(iter(q["criteria"])),
                                    "confidence": 0.9} for axis, q in questions.items()}
        canned["body"] = "private provider extension"
        mocks = self.tmp / "mocks.json"; mocks.write_bytes(canonical([canned]))
        args = ["ask", "--backend", "openrouter", "--state", str(state),
                "--mock-responses", str(mocks)]
        out = self.tmp / "router"
        self.assertEqual(main(args + ["--out", str(out)]), 0)
        report = json.loads((out / "results.json").read_text())
        self.assertEqual(report["backend"], "openrouter")
        self.assertEqual(report["model_requested"], openrouter.MODEL)
        self.assertEqual(report["models_seen"], [openrouter.RESPONSE_MODEL])
        self.assertEqual((report["input_tokens"], report["output_tokens"], report["cost"]), (7, 0, 0.001))
        for name in ("answer-0001.json", "answers.json", "results.json"):
            text = (out / name).read_text()
            self.assertNotIn("synthetic state", text)
            self.assertNotIn("private provider extension", text)
            self.assertIn('"backend": "openrouter"', text)
        manifest = self.tmp / "manifest.json"
        data = {"model": openrouter.MODEL, "backend": "openrouter",
                "quiz_sha256": sha256(state.read_bytes()), "questions_sha256": sha256(canonical(questions))}
        manifest.write_bytes(canonical(data))
        self.assertEqual(main(args + ["--manifest", str(manifest), "--out", str(self.tmp / "frozen")]), 0)
        for field, value in (("backend", "typesafe"), ("model", MODEL)):
            manifest.write_bytes(canonical(dict(data, **{field: value})))
            target = self.tmp / field
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                main(args + ["--manifest", str(manifest), "--out", str(target)])
            self.assertFalse(target.exists())
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            main(["replay", "--backend", "openrouter", "--fixture", str(ROOT / "examples/fixtures/fresh-100"),
                  "--out", str(self.tmp / "refused")])

    def test_green_and_red_controls(self):
        for choices, hits in [(["a", "b"], 2), (["a", "a"], 1)]:
            client = MockClient([response(c) for c in choices])
            answers = [client.ask("synthetic", Q).choice("purpose") for _ in choices]
            client.finish()
            self.assertEqual(metrics(["a", "b"], answers, ["a", "b"])["correct"], hits)
            self.assertEqual(client.input_tokens, 14)
            self.assertEqual(client.models_seen, {MODEL})
        self.assertFalse(gate(["a", "b"], ["a", "a"], [0.9, 0.9])["met"])
        self.assertTrue(gate(["a", "b"], ["a", "b"], [0.9, 0.9])["met"])

    def test_unused_null_mock_refused(self):
        client = MockClient([response(), None])
        client.ask("synthetic", Q)
        with self.assertRaises(ValueError):
            client.finish()

    def test_invalid_optional_probabilities_and_partial_checkpoint(self):
        questions = load_questions("work_purpose_v3")
        records = [{"id": name, "repo": "HiQS-Labs/pub", "state": "synthetic"}
                   for name in ("one", "two")]
        labels = [{"id": name, "purpose": "bug_fix", "area": "integrations"}
                  for name in ("one", "two")]
        records_file = self.tmp / "records.json"
        labels_file = self.tmp / "labels.json"
        manifest_file = self.tmp / "manifest.json"
        mocks_file = self.tmp / "mocks.json"
        records_file.write_bytes(canonical(records))
        labels_file.write_bytes(canonical(labels))
        manifest_file.write_bytes(canonical({"model": MODEL,
            "quiz_sha256": sha256(records_file.read_bytes()),
            "questions_sha256": sha256(canonical(questions)), **commit(labels_file),
            "gate": {"axis": "purpose", "confidence_floor": 0.8,
                     "min_accuracy": 0.9, "min_coverage": 0.6}}))
        def canned():
            return {"model": MODEL, "answers": {
                axis: {"type": "choice", "choice": choice, "confidence": 0.9}
                for axis, choice in (("purpose", "bug_fix"), ("area", "integrations"))}}
        first = canned()
        first["answers"]["area"]["probabilities"] = {"integrations": 0.8, "ui": 0.1}
        with self.assertRaises(ValueError):
            MockClient([first]).ask("synthetic", questions).probabilities("area")
        args = ["replay", "--records", str(records_file), "--labels", str(labels_file),
                "--manifest", str(manifest_file), "--mock-responses", str(mocks_file)]
        mocks_file.write_bytes(canonical([first, canned()]))
        out = self.tmp / "completed"
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(main(args + ["--out", str(out)]), 0)
        answers = json.loads((out / "answers.json").read_text())
        self.assertEqual(answers[0]["answers"]["area"]["probabilities_status"], "invalid")
        self.assertNotIn("probabilities", answers[0]["answers"]["area"])
        self.assertEqual(json.loads((out / "results.json").read_text())["axes"]["purpose"]["metrics"]["correct"], 2)
        self.assertEqual(json.loads((out / "answer-0001.json").read_text()), answers[0])

        failed = canned()
        failed["model"] = "wrong-model"
        mocks_file.write_bytes(canonical([first, failed]))
        partial = self.tmp / "partial"
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            main(args + ["--out", str(partial)])
        self.assertTrue((partial / "answer-0001.json").exists())
        self.assertFalse((partial / "answers.json").exists())
        self.assertFalse((partial / "results.json").exists())

    def test_all_states_checked_before_first_request(self):
        records = [{"id": "one", "repo": "HiQS-Labs/pub", "state": "synthetic"},
                   {"id": "two", "repo": "HiQS-Labs/pub", "state": {}}]
        record_file = self.tmp / "records.json"
        record_file.write_bytes(canonical(records))
        labels = self.tmp / "labels.json"; labels.write_text("[]")
        questions = load_questions("work_purpose_v3")
        manifest = self.tmp / "manifest.json"
        manifest.write_bytes(canonical({"model": MODEL,
            "quiz_sha256": sha256(record_file.read_bytes()),
            "questions_sha256": sha256(canonical(questions)), **commit(labels),
            "gate": {"axis": "purpose", "confidence_floor": 0.8,
                     "min_accuracy": 0.9, "min_coverage": 0.6}}))
        canned = json.loads((ROOT / "examples/fixtures/fresh-100/responses.json").read_text())[0]
        answer = MockClient([canned]).ask("synthetic", questions)
        args = ["eval", "--records", str(record_file), "--labels", str(labels),
                "--manifest", str(manifest), "--live", "--out", str(self.tmp / "out")]
        with patch.dict(os.environ, {"TYPESAFE_API_KEY": "test-only"}, clear=True), \
                patch("jev.cli.repo_visibility", return_value={"HiQS-Labs/pub": "PUBLIC"}), \
                patch.object(JevClient, "ask", return_value=answer) as ask, \
                contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            main(args)
        ask.assert_not_called()

    def test_empty_alignment_and_nonfinite_refused(self):
        for call in [lambda: metrics([], [], []), lambda: metrics(["a"], [], ["a"]),
                     lambda: gate([], [], []), lambda: confidence_table(["a"], ["a"], []),
                     lambda: gate(["a"], ["a"], [float("nan")]),
                     lambda: MockClient([response()]).ask(" ", Q),
                     lambda: MockClient([response()]).ask("synthetic", {}),
                     lambda: canonical({"bad": float("nan")})]:
            with self.assertRaises(ValueError):
                call()
        self.assertFalse(gate([None], ["a"], [1], min_accuracy=0, min_coverage=0)["met"])
        self.assertEqual(metrics([None], ["a"], ["a"])["macro_f1"], 0)

    def test_metric_universe_and_confidence_boundaries(self):
        m = metrics(["a", "b", "a", None, "c"], ["a", "b", "b", "a", "c"], ["a", "b", "d"])
        self.assertEqual(m["confusion_labels"], ["a", "b", "c", "d"])
        self.assertAlmostEqual(m["macro_f1"], (2 / 3 + 2 / 3 + 1) / 4)
        self.assertEqual(m["confusion"][0], [1, 1, 0, 0])
        with self.assertRaises(ValueError):
            metrics(["a"], ["outside"], ["a"])
        table = confidence_table(["a"] * 4, ["a"] * 4, [0, 0.5, 0.8, 1])
        self.assertEqual([r["n"] for r in table], [1, 1, 2])

    def test_hash_and_model_contract(self):
        answer = MockClient([response()]).ask("synthetic", Q)
        self.assertEqual(answer.request_sha256, sha256(canonical({"model": MODEL, "state": "synthetic", "questions": Q})))
        self.assertEqual(answer.response_sha256, sha256(canonical(response())))
        self.assertEqual(canonical({"b": 1, "a": "é"}), b'{"a":"\xc3\xa9","b":1}')
        for model in (None, "moving-model", "jev-1.12.0"):
            bad = response(); bad["model"] = model
            with self.assertRaises(ValueError):
                MockClient([bad]).ask("synthetic", Q)
        bad = response(); del bad["model"]
        with self.assertRaises(ValueError):
            MockClient([bad]).ask("synthetic", Q)
        with self.assertRaises(ValueError):
            JevClient("test-only", model="moving-model")

    def test_typed_accessors_and_missing_probabilities(self):
        r = response()
        r["answers"].update({"rating": {"type": "score", "score": 1.2, "confidence": 0.6},
                             "valid": {"type": "noul", "noul": 0.7}})
        a = Answer(r, "x", "y")
        self.assertEqual(a.choice("purpose"), "a")
        self.assertEqual(a.score("rating"), 1.2)
        self.assertEqual(a.noul("valid"), 0.7)
        self.assertEqual(a.probabilities("purpose"), {"a": 0.95, "b": 0.05})
        for call in [lambda: a.choice("rating"), lambda: a.confidence("valid"), lambda: a.probabilities("valid")]:
            with self.assertRaises(ValueError): call()
        with self.assertRaises(KeyError): a.probabilities("rating")
        r["answers"]["valid"]["noul"] = True
        with self.assertRaises(ValueError): a.noul("valid")

    def test_ordered_mocks_exhaustion_and_coverage(self):
        c = MockClient([response("b"), response("a")])
        self.assertEqual(c.ask("x", Q).choice("purpose"), "b")
        with self.assertRaises(ValueError): c.finish()
        with self.assertRaises(ValueError): MockClient([]).ask("x", Q)
        with self.assertRaises(ValueError): MockClient([response("outside")]).ask("x", Q)
        with self.assertRaises(ValueError): MockClient([response()]).ask("x", {**Q, "extra": Q["purpose"]})

    def test_no_key_and_ci_refusal(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ValueError): load_key()
        with self.assertRaises(ValueError): JevClient("")
        keyfile = self.tmp / "key"; keyfile.write_text("test-only\n")
        self.assertEqual(load_key(keyfile), "test-only")
        with patch.dict(os.environ, {"CI": "true"}):
            with self.assertRaises(ValueError): JevClient("test-only").ask("x", Q)

    def test_mock_transport_retry_and_raw_response_hash(self):
        raw = json.dumps(response(), indent=2).encode()
        def success():
            stream = io.BytesIO(raw)
            return stream
        for code in (429, 500, 529, 599):
            error = HTTPError("redacted", code, "redacted", {"retry-after": "3"}, None)
            with patch.dict(os.environ, {}, clear=True), patch("urllib.request.OpenerDirector.open", side_effect=[error, success()]) as send, patch("time.sleep") as sleep:
                answer = JevClient("test-only").ask("x", Q)
                self.assertEqual(send.call_count, 2)
                sleep.assert_called_once_with(3)
                self.assertEqual(answer.response_sha256, sha256(raw))
        for code, calls in [(401, 1), (503, 3)]:
            with patch.dict(os.environ, {}, clear=True), patch("urllib.request.OpenerDirector.open", side_effect=HTTPError("x", code, "secret", {}, None)) as send, patch("time.sleep"):
                with self.assertRaisesRegex(RuntimeError, f"^Jev HTTP {code}$"):
                    JevClient("test-only").ask("x", Q)
                self.assertEqual(send.call_count, calls)
        with patch.dict(os.environ, {}, clear=True), patch("time.time", return_value=0), patch("time.sleep") as sleep, patch("urllib.request.OpenerDirector.open", side_effect=[HTTPError("x", 429, "x", {"retry-after": "Thu, 01 Jan 1970 00:00:04 GMT"}, None), success()]):
            JevClient("test-only").ask("x", Q)
            sleep.assert_called_once_with(4)

    def test_freeze_commitment_and_recursive_denylist(self):
        labels = self.tmp / "labels.json"; labels.write_text("[]")
        commitment = commit(labels)
        self.assertTrue(verify(labels, commitment))
        verify_freeze(self.tmp, {labels.name: commitment["labels_sha256"]})
        labels.write_text("[1]")
        with self.assertRaises(ValueError): verify(labels, commitment)
        with self.assertRaises(ValueError): verify_freeze(self.tmp, {labels.name: commitment["labels_sha256"]})
        for field in ("title", "description", "stderr", "stdout", "body", "TITLE"):
            target = self.tmp / "refused.json"
            with self.assertRaises(ValueError): write_results(target, {"nested": [{field: "never persisted"}]})
            self.assertFalse(target.exists())
        write_results(self.tmp / "safe.json", {"correct": 1})
        with self.assertRaises(FileExistsError): write_results(self.tmp / "safe.json", {})
        for fixture in (ROOT / "examples/fixtures").glob("*/*.json"):
            safe_results(json.loads(fixture.read_text()))

    def test_malformed_repository_and_response_shapes_refused(self):
        for repo in (None, 7, {}, ""):
            with self.assertRaises(ValueError): repo_visibility([repo])
        for usage in (None, [], "invalid"):
            bad = response(); bad["usage"] = usage
            with self.assertRaises(ValueError): MockClient([bad]).ask("synthetic", Q)
        bad = response(); bad["answers"]["purpose"] = []
        with self.assertRaises(ValueError): MockClient([bad]).ask("synthetic", Q)

    def test_visibility_is_fail_closed(self):
        def runner(cmd, **kwargs):
            return type("Result", (), {"returncode": 0, "stdout": "PUBLIC\n" if cmd[3].casefold().endswith("/pub") else "PRIVATE\n"})()
        vis = repo_visibility(["HiQS-Labs/pub", "HiQS-Labs/private", "BinoidCBD/pub", "former-org/pub"], runner=runner)
        self.assertEqual(vis, {"HiQS-Labs/pub": "PUBLIC", "HiQS-Labs/private": "DENIED", "BinoidCBD/pub": "DENIED", "former-org/pub": "DENIED"})
        policy = {"allowed_owners": ["HiQS-Labs"], "denied_owners": [], "denied_repos": ["HiQS-Labs/pub"]}
        self.assertEqual(repo_visibility(["hiqs-labs/PUB"], policy, runner=runner), {"hiqs-labs/PUB": "DENIED"})

    def test_agreement_and_binary_threshold(self):
        file = self.tmp / "annotator.json"; file.write_text('{"one":"a","two":"b"}')
        self.assertEqual(agreement({"one": "a", "two": "a"}, file)["correct"], 1)
        with self.assertRaises(ValueError): agreement({"one": "a"}, file)
        report = fn_zero_threshold(["fail", "fail", "pass"], [0.05, 0.9, 0.05])
        self.assertEqual(report["threshold"], 0.05)
        self.assertEqual(report["false_positives"], 1)
        with self.assertRaises(ValueError): fn_zero_threshold(["pass"], [0.1])

    def test_frozen_question_sets(self):
        work = load_questions("work_purpose_v3")
        self.assertEqual(len(work["purpose"]["criteria"]), 8)
        self.assertEqual(len(work["area"]["criteria"]), 12)
        self.assertEqual(sha256(canonical(work)), "21094cd4f260f09986f70626d8991be8e9650c103bb107d3740d57219aed2821")
        triage = load_questions("ate_triage_v1")
        self.assertEqual(set(triage["severity"]["criteria"]), {"none", "low", "medium", "high", "critical"})
        self.assertEqual(set(triage["category"]["criteria"]), {"crash", "auth_failure", "bad_diff", "timeout", "no_edit", "config_error", "env_failure", "env_missing", "ok"})
        self.assertIn("even with exit_code 0", triage["status"]["instructions"])

    def test_ask_example_runs_offline_without_persisting_state(self):
        out = self.tmp / "ask"
        args = ["ask", "--state", str(ROOT / "examples/ask/ate-state.json"), "--questions", "ate_triage_v1",
                "--mock-responses", str(ROOT / "examples/ask/ate-mock-response.json"), "--out", str(out)]
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(main(args), 0)
        answers = json.loads((out / "answers.json").read_text())
        self.assertEqual(answers[0]["answers"]["status"]["choice"], "fail")
        self.assertNotIn("probabilities", answers[0]["answers"]["status"])
        for name in ("answers.json", "results.json"):
            self.assertNotIn("Segmentation fault", (out / name).read_text())

    def test_receipt_replays_and_labels_after_answers(self):
        for name, correct in [("purpose-40", 37), ("fresh-100", 88)]:
            fixture = ROOT / "examples/fixtures" / name
            out = self.tmp / name
            args = ["replay", "--fixture", str(fixture), "--out", str(out)]
            original = Path.read_text
            original_bytes = Path.read_bytes
            def read_bytes(path, *a, **kw):
                if path == fixture / "labels.json":
                    self.assertTrue((out / "answers.json").exists())
                return original_bytes(path, *a, **kw)
            def read(path, *a, **kw):
                if path == fixture / "labels.json":
                    self.assertTrue((out / "answers.json").exists())
                return original(path, *a, **kw)
            with patch.object(Path, "read_text", read), patch.object(Path, "read_bytes", read_bytes), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main(args), 0)
            self.assertEqual((out / "results.json").read_bytes(), (fixture / "expected.json").read_bytes())
            report = json.loads((out / "results.json").read_text())
            self.assertEqual(report["axes"]["purpose"]["metrics"]["correct"], correct)
            if name == "purpose-40":
                self.assertEqual(report["axes"]["area"]["metrics"]["correct"], 32)
                self.assertEqual(report["axes"]["area"]["metrics"]["labeled_n"], 38)
            if name == "fresh-100":
                self.assertEqual(report["gate"]["high_confidence_correct"], 73)
                self.assertEqual(report["gate"]["high_confidence_rows"], 75)
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit): main(args)

    def test_benchmark_replay_and_probability_limit(self):
        fixture = ROOT / "examples/fixtures/ate-benchmark"
        out = self.tmp / "benchmark"
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(main(["replay", "--fixture", str(fixture), "--out", str(out)]), 0)
        report = json.loads((out / "results.json").read_text())["benchmark"]
        self.assertEqual(report["false_negatives"], 1)
        self.assertEqual(report["false_positives"], 0)
        self.assertEqual(report["tier1_agreement"], {"agree": 65, "anomaly": 9})
        self.assertIsNone(report["fn_zero_threshold"])
        self.assertEqual(report["recorded_fn_zero_threshold"], 0.48)
        self.assertFalse(report["fn_floor_met"])
        self.assertEqual(binary_counts(["pass", "fail"], ["pass", "fail"])["false_negatives"], 0)
        self.assertEqual(binary_counts(["pass", "fail"], ["pass", "pass"])["false_negatives"], 1)
        self.assertFalse(binary_counts(["pass"], ["pass"])["fn_floor_met"])

    def test_confusion_reconstruction_refuses_empty_or_invalid(self):
        for matrix in ([[0]], [[-1]], [[True]], [[1, 0]]):
            with self.assertRaises(ValueError): metrics_from_confusion(matrix, ["a"])
        self.assertEqual(metrics_from_confusion([[2, 1], [0, 1]], ["a", "b"])["correct"], 3)


if __name__ == "__main__":
    unittest.main()
