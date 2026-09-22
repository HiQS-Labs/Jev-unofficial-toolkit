# Cases for code adapted from jbt95/jev-toolkit f8792f9, MIT; see ../NOTICE and ../licenses/MIT-jev-toolkit.txt.
"""Offline tests for redaction, the loop breaker, skill routing, and repeat drift."""
import contextlib
import io
import json
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch

from jev.answers import MODEL
from jev.cli import main
from jev.client import MockClient
from jev.eval import drift
from jev.guard import load_questions
from jev.loops import ESCALATE_AT, PRUNE_SECONDS, LoopGuard, fingerprint, identity_request, matched_fingerprint
from jev.routing import NO_SKILL, route, route_request
from jev.text import clip, redact, sanitize, strip_fenced_code

Q = {"purpose": {"type": "choice", "instructions": "Choose a or b.", "criteria": {"a": "A", "b": "B"}}}


def response(choice="a", confidence=0.9):
    return {"model": MODEL, "usage": {"input_tokens": 7}, "answers": {
        "purpose": {"type": "choice", "choice": choice, "confidence": confidence}}}


class BorrowedTests(unittest.TestCase):
    def setUp(self):
        self.stack = contextlib.ExitStack()
        self.addCleanup(self.stack.close)
        for target in ("socket.socket.connect", "socket.create_connection", "urllib.request.urlopen",
                       "urllib.request.OpenerDirector.open", "subprocess.run", "subprocess.Popen"):
            self.stack.enter_context(patch(target, side_effect=AssertionError("network/process forbidden in tests")))
        self.tmp = Path(self.stack.enter_context(tempfile.TemporaryDirectory()))

    def test_redaction_masks_credentials_code_and_length(self):
        text = 'OPENAI_API_KEY=sk-live-123\n"password": "hunter2"\nAuthorization: Bearer abcdef123456\nkeep this'
        out = redact(text)
        for secret in ("sk-live-123", "hunter2", "abcdef123456"):
            self.assertNotIn(secret, out)
        self.assertIn("keep this", out)
        self.assertEqual(strip_fenced_code("before\n```py\nsecret()\n```\nafter"), "before\n[code]\nafter")
        self.assertEqual(strip_fenced_code("open\n~~~\nnever closed"), "open\n[code]")
        self.assertTrue(clip("x" * 10, 4).endswith("[clipped]"))
        self.assertEqual(sanitize({"a": ["token=abc"], "n": 3, "b": None}), {"a": ["token=[redacted]"], "n": 3, "b": None})

    def test_cli_redact_changes_what_is_sent(self):
        state = self.tmp / "state.json"
        state.write_text(json.dumps({"log": "api_key=sk-secret-value"}))
        mocks = self.tmp / "mocks.json"
        mocks.write_text(json.dumps([response()]))
        sent = []
        original = MockClient.ask
        def spy(client, s, q):
            sent.append(json.dumps(s))
            return original(client, s, q)
        with patch.object(MockClient, "ask", spy), \
                patch("jev.cli.load_questions", return_value=Q), contextlib.redirect_stdout(io.StringIO()):
            main(["ask", "--state", str(state), "--mock-responses", str(mocks), "--out", str(self.tmp / "a"), "--redact"])
            main(["ask", "--state", str(state), "--mock-responses", str(mocks), "--out", str(self.tmp / "b")])
        self.assertNotIn("sk-secret-value", sent[0])
        self.assertIn("sk-secret-value", sent[1])
        self.assertTrue(json.loads((self.tmp / "a/results.json").read_text())["redacted"])

    def test_loop_guard_escalates_once_and_prunes(self):
        now = [1000.0]
        guard = LoopGuard(self.tmp / "loops.json", clock=lambda: now[0])
        fp = fingerprint("  Build   FAILED\n")
        self.assertEqual(fp, fingerprint("build failed"))
        results = [guard.check(fp, "Build failed") for _ in range(ESCALATE_AT + 1)]
        self.assertEqual([r["escalate"] for r in results], [False, False, True, False])
        self.assertEqual(guard.recent(5), [{"fingerprint": fp, "sample": "Build failed"}])
        now[0] += PRUNE_SECONDS + 1
        self.assertEqual(guard.check(fp)["count"], 1)
        self.assertEqual(list(self.tmp.glob("*.tmp")), [])
        (self.tmp / "loops.json").write_text("  \n")
        self.assertEqual(guard.recent(5), [])
        (self.tmp / "loops.json").write_text('{"x": {"count": "1"}}')
        with self.assertRaises(ValueError):
            guard.check(fp)

    def test_loop_guard_concurrent_checks_lose_no_counts(self):
        guard = LoopGuard(self.tmp / "shared.json")
        threads = [threading.Thread(target=guard.check, args=("fp",)) for _ in range(20)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        self.assertEqual(guard.check("fp")["count"], 21)

    def test_identity_request_keeps_text_in_state(self):
        recent = [{"fingerprint": "aaa", "sample": "token=abc timeout"}, {"fingerprint": "bbb", "sample": "disk full"}]
        state, questions = identity_request("password=pw timeout again", recent)
        self.assertEqual(set(questions["same_as"]["criteria"]), {"recent_0", "recent_1", "none"})
        self.assertNotIn("timeout", json.dumps(questions))
        self.assertNotIn("pw timeout", state["current"])
        self.assertNotIn("abc", state["recent_0"])
        self.assertEqual(matched_fingerprint(recent, "recent_1"), "bbb")
        self.assertIsNone(matched_fingerprint(recent, "none"))
        for bad in ("recent_2", "recent_x", "other"):
            with self.assertRaises(ValueError):
                matched_fingerprint(recent, bad)
        with self.assertRaises(ValueError):
            identity_request("new failure", [])

    def test_failure_triage_is_frozen(self):
        q = load_questions("failure_triage_v1")
        self.assertEqual({k: v["type"] for k, v in q.items()},
                         {"failure_class": "choice", "blocks_work": "noul", "safe_to_suppress": "noul"})
        self.assertIn("security_finding", q["failure_class"]["criteria"])

    def test_skill_routing_floors(self):
        candidates = {"deploy": "Ship a release\n to production", "docs": "Write docs"}
        state, questions = route_request("ship it, api_key=abc", candidates)
        self.assertEqual(set(questions["skill"]["criteria"]), {"deploy", "docs", NO_SKILL})
        self.assertEqual(questions["skill"]["criteria"]["deploy"], "Ship a release to production")
        self.assertNotIn("abc", state["task"])
        with self.assertRaises(ValueError):
            route_request("x", {NO_SKILL: "clash"})
        def answers(pick, conf=0.9, dep=3, second=0.7):
            return {"skill": {"type": "choice", "choice": pick, "confidence": conf},
                    "dependence": {"type": "score", "score": dep, "confidence": 0.9},
                    "second": {"type": "noul", "noul": second}}
        self.assertEqual(route(candidates, answers("deploy")),
                         {"route": "deploy", "reason": "routed", "second_needed": True, "confidence": 0.9, "dependence": 3.0})
        for pick, conf, dep, reason in (("none", 0.9, 3, "no-match"), ("ghost", 0.9, 3, "unknown-skill"),
                                        ("deploy", 0.4, 3, "low-confidence"), ("deploy", 0.9, 1, "low-dependence")):
            self.assertEqual(route(candidates, answers(pick, conf, dep))["reason"], reason)

    def test_drift_and_cli_repeat(self):
        runs = [{"purpose": {"type": "choice", "choice": c, "confidence": p}} for c, p in (("a", 0.9), ("a", 0.8), ("b", 0.6))]
        report = drift(runs, Q)["purpose"]
        self.assertEqual(report["distinct"], 2)
        self.assertAlmostEqual(report["modal_share"], 2 / 3)
        self.assertAlmostEqual(report["confidence_range"], 0.3)
        noul = {"x": {"type": "noul", "instructions": "x"}}
        self.assertAlmostEqual(drift([{"x": {"noul": 0.2}}, {"x": {"noul": 0.7}}], noul)["x"]["range"], 0.5)
        with self.assertRaises(ValueError):
            drift(runs[:1], Q)
        state = self.tmp / "state.json"
        state.write_text(json.dumps({"t": "x"}))
        mocks = self.tmp / "mocks.json"
        mocks.write_text(json.dumps([response("a"), response("b", 0.5), response("a")]))
        out = self.tmp / "rep"
        with patch("jev.cli.load_questions", return_value=Q), contextlib.redirect_stdout(io.StringIO()):
            main(["ask", "--state", str(state), "--mock-responses", str(mocks), "--out", str(out), "--repeat", "3"])
        report = json.loads((out / "results.json").read_text())
        self.assertEqual(report["repeat"], 3)
        self.assertEqual(report["drift"]["ask"]["purpose"]["distinct"], 2)
        self.assertEqual(len(json.loads((out / "answers.json").read_text())), 1)
        self.assertEqual(sorted(p.name for p in out.glob("answer-*")), ["answer-0001-r2.json", "answer-0001-r3.json", "answer-0001.json"])
        for bad in ("0", "11"):
            with self.assertRaises(SystemExit), contextlib.redirect_stderr(io.StringIO()):
                main(["ask", "--state", str(state), "--mock-responses", str(mocks), "--out", str(self.tmp / bad), "--repeat", bad])
        fixture = Path(__file__).resolve().parents[1] / "examples/fixtures/purpose-40"
        with self.assertRaises(SystemExit), contextlib.redirect_stderr(io.StringIO()):
            main(["replay", "--fixture", str(fixture), "--out", str(self.tmp / "fx"), "--repeat", "2"])


if __name__ == "__main__":
    unittest.main()
