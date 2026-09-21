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
from jev.answers import Answer, MODEL, pinned_model
from jev.client import JevClient, MockClient, canonical, load_key, sha256, validate_questions
from jev.cli import main, score
from jev.eval import (agreement, confidence_table, fn_zero_threshold, gate, metrics, metrics_from_confusion,
                      binary_counts, noul_metrics, score_metrics, within)
from jev.guard import (append_decision, commit, decision_record, load_questions, repo_visibility, safe_results,
                       verify, verify_freeze, write_results)
from jev.policy import decide

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
        questions = dict(Q,
                         rating={"type": "score", "instructions": "Rate.", "criteria": ["low", "high", "high+"]},
                         valid={"type": "noul", "instructions": "Is it valid?"})
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
        for model in (None, MODEL, openrouter.MODEL, "typesafe/jev-1.14",
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
        with self.assertRaises(ValueError): openrouter.OpenRouterClient("test", model="typesafe/jev-1.14")
        with self.assertRaises(ValueError): JevClient("test", endpoint=openrouter.ENDPOINT)
        canned = self.router_response()
        canned["answers"] = {"rating": {"type": "score", "score": 2, "confidence": 0.8}}
        with self.assertRaises(ValueError):
            openrouter.OpenRouterMockClient([canned]).ask(
                "synthetic", {"rating": {"type": "score", "instructions": "Rate.", "criteria": ["low", "high"]}})

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
            if fixture.name != "records.json":  # inputs carry `state` by definition; results never do
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

    GATE = {"default": "confirm", "clauses": [
        {"decision": "block", "any": [{"rule": "denylist"},
                                      {"axis": "approval_mode", "choice": "block", "min_confidence": 0.9},
                                      {"all": [{"axis": "risk_level", "min": 2.5},
                                               {"axis": "likely_sensitive_change", "min": 0.85}]}]},
        {"decision": "confirm", "any": [{"rule": "protected_path"},
                                        {"axis": "approval_mode", "choice": "confirm", "min_confidence": 0.75},
                                        {"axis": "scope_matches_task", "max": 0.65},
                                        {"axis": "risk_level", "min": 1.5}]},
        {"decision": "allow", "all": [{"rule": "allowlist"},
                                      {"axis": "approval_mode", "choice": "allow", "min_confidence": 0.85},
                                      {"axis": "scope_matches_task", "min": 0.8}]}]}

    @staticmethod
    def gate_answers(mode="allow", conf=0.9, risk=0.5, scope=0.9, sensitive=0.1):
        return {"approval_mode": {"type": "choice", "choice": mode, "confidence": conf},
                "risk_level": {"type": "score", "score": risk, "confidence": 0.8},
                "scope_matches_task": {"type": "noul", "noul": scope},
                "likely_sensitive_change": {"type": "noul", "noul": sensitive}}

    def bundle_eval(self, responses, labels, manifest_extra, questions="agent_action_gate_v1"):
        """Run an offline `eval` of the three-primitive bundle; returns (exit_code, out_dir)."""
        q = load_questions(questions)
        records = [{"id": r["id"], "repo": "HiQS-Labs/pub", "state": {"n": i}} for i, r in enumerate(labels)]
        record_file = self.tmp / "records.json"; record_file.write_bytes(canonical(records))
        label_file = self.tmp / "labels.json"; label_file.write_bytes(canonical(labels))
        mocks = self.tmp / "mocks.json"; mocks.write_bytes(canonical(responses))
        manifest = self.tmp / "manifest.json"
        manifest.write_bytes(canonical({"model": MODEL, "quiz_sha256": sha256(record_file.read_bytes()),
            "questions_sha256": sha256(canonical(q)), **commit(label_file), **manifest_extra}))
        out = self.tmp / "out"
        args = ["eval", "--records", str(record_file), "--labels", str(label_file), "--questions", questions,
                "--manifest", str(manifest), "--mock-responses", str(mocks), "--out", str(out)]
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            try:
                return main(args), out
            except SystemExit as stop:
                return stop.code, out

    def test_pinned_model_refuses_aliases(self):
        self.assertEqual(pinned_model("jev-1.14.0"), "jev-1.14.0")
        for alias in ("jev-latest", "jev-1", "jev-1.13", "1.13.0", "", None):
            with self.assertRaises(ValueError): pinned_model(alias)
        self.assertEqual(MODEL, "jev-1.13.0")

    def test_question_schema_refusals(self):
        good = {"c": {"type": "choice", "instructions": "Choose.", "criteria": {"a": "A"}},
                "s": {"type": "score", "instructions": "Rate.", "criteria": ["low", "high"]},
                "n": {"type": "noul", "instructions": "Is it?"}}
        self.assertIs(validate_questions(good), good)
        bad = [
            {"c": {"type": "choice", "criteria": {"a": "A"}}},                               # no instructions
            {"c": {"type": "rank", "instructions": "x", "criteria": {"a": "A"}}},            # unknown type
            {"c": {"type": "choice", "instructions": "x", "criteria": {"": "A"}}},           # empty label
            {"c": {"type": "choice", "instructions": "x", "criteria": {"a": ""}}},           # empty gloss
            {"c": {"type": "choice", "instructions": "x", "criteria": ["a"]}},              # list, not dict
            {"s": {"type": "score", "instructions": "x", "criteria": ["only"]}},             # one level
            {"s": {"type": "score", "instructions": "x", "criteria": {"0": "low"}}},         # dict, not list
            {"n": {"type": "noul", "instructions": "x", "criteria": ["y"]}},                 # noul with criteria
            {"": {"type": "noul", "instructions": "x"}},                                     # empty name
        ]
        for questions in bad:
            with self.assertRaises(ValueError): validate_questions(questions)
        with self.assertRaises(ValueError): MockClient([{"model": MODEL, "answers": {"s": {"type": "score", "score": 1.5, "confidence": 0.5}}}]).ask("x", {"s": good["s"]})
        self.assertEqual(MockClient([{"model": MODEL, "answers": {"s": {"type": "score", "score": 1.0, "confidence": 0.5}}}]).ask("x", {"s": good["s"]}).score("s"), 1.0)

    def test_score_and_noul_metrics_and_gate(self):
        m = score_metrics([0, 2, None, 3], [0.4, 2.6, 1.0, 1.0], 0.5)
        self.assertEqual((m["labeled_n"], m["uncertain_truth_n"], m["correct"]), (3, 1, 1))
        self.assertAlmostEqual(m["mae"], (0.4 + 0.6 + 2.0) / 3)
        with self.assertRaises(ValueError): score_metrics([0], [0.1], -0.1)
        n = noul_metrics([True, False, None, True], [0.9, 0.6, 0.5, 0.2], 0.5)
        self.assertEqual((n["labeled_n"], n["uncertain_truth_n"], n["correct"]), (3, 1, 1))
        self.assertAlmostEqual(n["brier"], (0.01 + 0.36 + 0.64) / 3)
        with self.assertRaises(ValueError): noul_metrics([1], [0.5], 0.5)      # non-boolean truth
        with self.assertRaises(ValueError): noul_metrics([True], [1.5], 0.5)   # probability outside unit
        g = gate([1, 2], [1.5, 2.6], [0.9, 0.9], 0.8, 0.9, 0.6, hit=within(0.5))
        self.assertEqual(g["high_confidence_correct"], 1)
        self.assertEqual(gate([1, 2], [1.5, 2.5], [0.9, 0.9], hit=within(0.5))["high_confidence_correct"], 2)
        self.assertEqual(confidence_table([1], [1.4], [0.95], within(0.5))[2]["correct"], 1)
        with self.assertRaises(ValueError):
            score([{"id": "a", "answers": {"rating": {
                "type": "score", "score": 1.0, "confidence": 0.9}}}],
                  [{"id": "a", "rating": 2}],
                  {"rating": {"type": "score", "instructions": "Rate.", "criteria": ["low", "high"]}},
                  {"axis": "rating", "confidence_floor": 0.8, "min_accuracy": 0.9, "min_coverage": 0.6},
                  scoring={"score_tolerance": 0.5})

    def test_bundle_eval_requires_registered_parameters(self):
        labels = [{"id": "a", "approval_mode": "block", "risk_level": 3, "scope_matches_task": False, "likely_sensitive_change": True},
                  {"id": "b", "approval_mode": "allow", "risk_level": 0, "scope_matches_task": True, "likely_sensitive_change": None}]
        responses = [{"model": MODEL, "answers": self.gate_answers("block", 0.93, 2.8, 0.21, 0.97)},
                     {"model": MODEL, "answers": self.gate_answers("allow", 0.9, 0.4, 0.85, 0.05)}]
        gate_cfg = {"gate": {"axis": "risk_level", "confidence_floor": 0.8, "min_accuracy": 0.9, "min_coverage": 0.6}}
        code, out = self.bundle_eval(responses, labels, {**gate_cfg, "score_tolerance": 0.5, "noul_threshold": 0.5})
        self.assertEqual(code, 0)
        report = json.loads((out / "results.json").read_text())
        self.assertEqual(report["axes"]["approval_mode"]["metrics"]["correct"], 2)
        self.assertEqual(report["axes"]["risk_level"]["metrics"]["correct"], 2)
        self.assertEqual(report["axes"]["scope_matches_task"]["metrics"]["correct"], 2)
        self.assertEqual(report["axes"]["likely_sensitive_change"]["metrics"]["labeled_n"], 1)
        self.assertNotIn("confidence_buckets", report["axes"]["scope_matches_task"])
        self.assertTrue(report["gate"]["met"])
        self.assertEqual(report["predictions"][0]["risk_level_score"], 2.8)
        self.assertEqual(report["predictions"][0]["scope_matches_task_noul"], 0.21)
        for missing in ({**gate_cfg, "noul_threshold": 0.5}, {**gate_cfg, "score_tolerance": 0.5}):
            self.tmp = Path(self.stack.enter_context(tempfile.TemporaryDirectory()))
            code, out = self.bundle_eval(responses, labels, missing)
            self.assertEqual(code, 2)
            self.assertFalse((out / "answers.json").exists())  # refused before any request
        self.tmp = Path(self.stack.enter_context(tempfile.TemporaryDirectory()))
        code, _ = self.bundle_eval(responses, labels, {"gate": {**gate_cfg["gate"], "axis": "scope_matches_task"},
                                                       "score_tolerance": 0.5, "noul_threshold": 0.5})
        self.assertEqual(code, 2)  # noul cannot be a gate axis
        self.tmp = Path(self.stack.enter_context(tempfile.TemporaryDirectory()))
        code, out = self.bundle_eval(responses, labels, {**gate_cfg, "scored_axes": ["approval_mode"], "score_tolerance": 0.5})
        self.assertEqual(code, 2)  # gate axis excluded by scored_axes must refuse, not silently drop the gate
        self.assertFalse((out / "answers.json").exists())
        for selected in ([], "risk_level", ["missing"], ["risk_level", "risk_level"]):
            self.tmp = Path(self.stack.enter_context(tempfile.TemporaryDirectory()))
            code, out = self.bundle_eval(responses, labels, {
                **gate_cfg, "scored_axes": selected, "score_tolerance": 0.5, "noul_threshold": 0.5})
            self.assertEqual(code, 2)
            self.assertFalse((out / "answers.json").exists())

    def test_frozen_set_with_valid_hash_but_invalid_shape_refused(self):
        bad = canonical({"n": {"type": "noul", "instructions": "x", "criteria": []}})
        (self.tmp / "bad.json").write_bytes(bad)
        (self.tmp / "bad.sha256").write_text(sha256(bad) + "\n")
        with patch.dict("jev.guard.FROZEN_QUESTIONS", {"bad": sha256(bad)}):
            with self.assertRaises(ValueError): load_questions("bad", self.tmp)

    def test_decision_log_is_typed_and_append_only(self):
        q = load_questions("agent_action_gate_v1")
        answer = MockClient([{"model": MODEL, "answers": self.gate_answers("block", 0.93, 2.8, 0.21, 0.97)}]).ask(
            {"task": "secret text", "command": "rm -rf /"}, q)
        record = decision_record("jev-agent-action-gate", "0.1.0", answer, q, "block", ["denylist"],
                                 policy=self.GATE, latency_ms=12, created_at="2026-09-20T00:00:00+00:00")
        self.assertEqual(record["input_fingerprint"], "sha256:" + answer.request_sha256)
        self.assertEqual(record["question_bundle_version"], sha256(canonical(q)))
        self.assertEqual(record["confidence"], {"approval_mode": 0.93, "risk_level": 0.8})
        self.assertEqual(record["probabilities"], {})
        self.assertEqual(record["policy_sha256"], decide(self.GATE, record["answers"])["policy_sha256"])
        log = self.tmp / "decisions.jsonl"
        append_decision(log, record); append_decision(log, {**record, "outcome_label": "confirmed"})
        lines = log.read_text().splitlines()
        self.assertEqual(len(lines), 2)
        self.assertNotIn("secret text", log.read_text()); self.assertNotIn("rm -rf", log.read_text())
        self.assertEqual(json.loads(lines[1])["outcome_label"], "confirmed")
        for bad in ({**record, "state": {}}, {**record, "nested": [{"command": "x"}]}, {**record, "latency_ms": float("nan")}):
            with self.assertRaises(ValueError): append_decision(log, bad)
        self.assertEqual(len(log.read_text().splitlines()), 2)
        with self.assertRaises(ValueError): decision_record("", "0.1.0", answer, q, "block")
        with self.assertRaises(ValueError): decision_record("s", "0.1.0", answer, q, "block", latency_ms=-1)
        with self.assertRaises(ValueError): decision_record("s", "0.1.0", answer, q, "block", executed_action=7)
        with self.assertRaises(ValueError): write_results(self.tmp / "leak.json", {"answers": [{"state": {}}]})

    def test_policy_first_match_and_fail_closed(self):
        cases = [
            (self.gate_answers(), ["allowlist"], "allow", 2),
            (self.gate_answers(), [], "confirm", None),                                   # no allowlist hit → default
            (self.gate_answers(scope=0.79), ["allowlist"], "confirm", None),              # scope just under allow floor
            (self.gate_answers(risk=1.5), ["allowlist"], "confirm", 1),                   # risk at confirm edge
            (self.gate_answers(scope=0.65), ["allowlist"], "confirm", 1),                 # scope at confirm edge
            (self.gate_answers("confirm", 0.75), ["allowlist"], "confirm", 1),
            (self.gate_answers("block", 0.9), ["allowlist"], "block", 0),
            (self.gate_answers("block", 0.89), ["allowlist"], "confirm", None),           # block below floor → fail-closed default
            (self.gate_answers(risk=2.5, sensitive=0.85), ["allowlist"], "block", 0),
            (self.gate_answers(risk=2.5, sensitive=0.84), ["allowlist"], "confirm", 1),
            (self.gate_answers(), ["denylist", "allowlist"], "block", 0),                 # deterministic rule wins
            ({"other": {"type": "choice", "choice": "x", "confidence": 1.0}}, ["allowlist"], "confirm", None),
        ]
        for answers, hits, decision, clause in cases:
            result = decide(self.GATE, answers, hits)
            self.assertEqual((result["decision"], result["clause"]), (decision, clause), (answers, hits))
        self.assertEqual(len(decide(self.GATE, {})["policy_sha256"]), 64)
        for bad in ({"clauses": []}, {"default": "x", "clauses": [{"decision": "y"}]},
                    {"default": "x", "clauses": [{"decision": "y", "any": []}]},
                    {"default": "x", "clauses": [{"decision": "y", "all": [{"axis": "a"}]}]},
                    {"default": "x", "clauses": [{"decision": "y", "all": [{"axis": "a", "min": "1"}]}]},
                    {"default": "x", "clauses": [{"decision": "y", "any": [{"rule": ""}]}]}):
            with self.assertRaises(ValueError): decide(bad, {})
        numeric = {"default": "confirm", "clauses": [
            {"decision": "allow", "all": [{"axis": "risk", "min": 1}]}]}
        for malformed in (True, "2", float("nan"), float("inf")):
            self.assertEqual(decide(numeric, {"risk": {"type": "score", "score": malformed}})["decision"], "confirm")
        self.assertEqual(decide(numeric, {"risk": {"type": [], "score": 2}})["decision"], "confirm")
        confidence = {"default": "confirm", "clauses": [
            {"decision": "allow", "all": [{"axis": "scope", "min_confidence": 0.5}]}]}
        self.assertEqual(decide(confidence, {"scope": {
            "type": "noul", "noul": 0.9, "confidence": 1.0}})["decision"], "confirm")

    def test_gate_example_runs_offline_without_persisting_state(self):
        out = self.tmp / "gate"
        args = ["ask", "--state", str(ROOT / "examples/ask/gate-state.json"), "--questions", "agent_action_gate_v1",
                "--mock-responses", str(ROOT / "examples/ask/gate-mock-response.json"), "--out", str(out)]
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(main(args), 0)
        answers = json.loads((out / "answers.json").read_text())
        self.assertEqual(len(answers), 1)
        got = answers[0]["answers"]
        self.assertEqual({k: v["type"] for k, v in got.items()},
                         {"approval_mode": "choice", "risk_level": "score", "scope_matches_task": "noul", "likely_sensitive_change": "noul"})
        self.assertIsInstance(got["risk_level"]["score"], float); self.assertTrue(0 <= got["risk_level"]["score"] <= 3)
        for axis in ("scope_matches_task", "likely_sensitive_change"):
            self.assertTrue(0 <= got[axis]["noul"] <= 1)
        for key in ("request_sha256", "response_sha256"):
            self.assertRegex(answers[0][key], r"^[0-9a-f]{64}$")
        state = json.loads((ROOT / "examples/ask/gate-state.json").read_text())
        for name in ("answers.json", "results.json"):
            text = (out / name).read_text()
            for secret in (state["task"], state["operation"]["command"], state["diff_summary"]):
                self.assertNotIn(secret, text)

    def test_frozen_question_sets(self):
        work = load_questions("work_purpose_v3")
        self.assertEqual(len(work["purpose"]["criteria"]), 8)
        self.assertEqual(len(work["area"]["criteria"]), 12)
        self.assertEqual(sha256(canonical(work)), "21094cd4f260f09986f70626d8991be8e9650c103bb107d3740d57219aed2821")
        gate_q = load_questions("agent_action_gate_v1")
        self.assertEqual({k: v["type"] for k, v in gate_q.items()},
                         {"approval_mode": "choice", "risk_level": "score", "scope_matches_task": "noul", "likely_sensitive_change": "noul"})
        self.assertEqual(len(gate_q["risk_level"]["criteria"]), 4)
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
