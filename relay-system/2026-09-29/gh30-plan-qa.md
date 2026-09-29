# RELAY · GH-30 plan QA: bounded concurrent dispatch
<!--
  Single source of truth for this two-agent relay. Read the ENTIRE file before acting.
  Scaffolded by relay-automation/new-relay.sh on 2026-09-29.
-->

NEXT: Reviewer
STATUS: Open
ROUND: 1 / 3

## ▶ TAKE YOUR TURN — read this first (works for ANY agent: Claude, Codex, agy)
1. **Read this whole file** (header, Setup, Ground rules, every block in the Log).
2. **Check it's your turn:** `NEXT` (top) names the role to act. Confirm you are bound to it and the
   last Log block isn't already yours. If not → STOP and reply "wrong window — nudge the <other> window."
3. **Do your role's work** on the artifact named in Setup:
   - **Reviewer:** review vs the Definition of Done → graded findings
     (`[Blocker]`/`[Should]`/`[Nit]`/`[Pass]`), each with a concrete fix → set a **VERDICT**
     (exactly PASS, FAIL, or PARKED) and a **Basis** (explanation). **Review the whole file, not just the diff** (GH-268):
     a beta test had this loop reach `Approved` in two rounds while an independent audit of the same
     branch found 20 issues (1 critical, 4 high) — every one of them in the pre-existing code the
     change sat on, which nobody had read. Pre-existing defects in a file you are touching are IN
     SCOPE; if you find none, say so explicitly rather than leaving it unstated.
     **Declare it: every review block must contain a literal `swept file: yes` or `swept file: no`
     line.** Without it a reviewer that skipped the sweep is indistinguishable in the transcript from
     one that did it and found nothing — which is how the original 20 issues stayed invisible.
     Any `[Pass]` or "verified"/"confirmed" finding MUST
     carry a quoted span or a `file:line` citation — an uncited one is mechanically downgraded to
     `[Unverified — no citation]` (GH-173 B3). Do **not** edit the artifact; only append findings here.
     **A finding that asks for a behaviour change is a generalization unless you can paste the concrete
     input — a row, a value, a `file:line` — that fails under the current code** (GH-681: the gh673
     final QA relay generalized one late-error observation into "or a later invalid identity", the
     Producer implemented it, the same seat `[Pass]`ed it next round, and one historical NULL-URL
     ledger row then blanked every issue). Every `[Blocker]` or `[Should]` requesting a behaviour
     change MUST carry three lines: `Observed input:` (the failing input you saw), `Affected scope:`
     (the input predicate the change would govern), `Falsifier:` (the fixture or data that would show
     the change unnecessary or wrong, and its expected result).
     A `[Blocker]` must cite an observed failure. This is a protocol rule, not a mechanical check —
     the Producer may disposition a request lacking these as `Declined — unproven generalization`.
   - **Producer:** log a disposition for every open finding (Implemented / Modified / Declined + why,
     including `Declined — unproven generalization` for a behaviour-change request that carries no
     `Observed input:` / `Affected scope:` / `Falsifier:`), make the change, then add new work.
4. **Append ONE block** at the very bottom, directly **above** the marker line. Never edit earlier turns.
   Reviewer headings may be `### Reviewer · Round N`, `### Round N · Reviewer · <agent>`, `### Reviewer (<agent>)` (optionally followed by `— rN`), or `### Reviewer — Round N` (optionally followed by `(<agent>)`); follow the heading with a non-empty review body.
5. **Update the header:** flip `NEXT`; set `STATUS` (`Approved` closes — Reviewer only; else `Open`);
   the Producer bumps `ROUND` when opening a new cycle. If the max `ROUND` ends without `Approved`,
   set `STATUS: Escalated`.
6. **Commit only the relay file** (`relay(gh30-plan-qa): <role> r<N>`); no push. **Stop** and report one line.
7. **Hand off explicitly — EVERY turn, not just the first** (GH-268). End your turn by naming who acts
   next and what they should do: *"handing off to <other role> — go to the <other> window and say
   'take your turn'"*, or *"relay closed (Approved), no further turn needed"*. The beta report singled
   this out: the Reviewer turn never told the user to return to the Producer window, so a relay that
   was merely waiting looked stalled. A turn that ends without this line is not finished.

## Setup
- Artifact under review: `PROJECT/2-WORKING/GH-30-BOUNDED-CONCURRENCY.md` in the TARGET repo (Jev-unofficial-toolkit, commit c3d9c36). Read it in full, then the code it cites: `jev/cli.py` (esp. `run`, lines 99-265), `jev/client.py` (`_answer`, `ask`, `MockClient`), `jev/openrouter.py` (answer handling, counters, mock client), `tests/test_jev_harness.py` (network-blocking patches, checkpoint tests near lines 164-250, live-path patches near 265).
- Reviewer: codex   ·   Producer: claude-a
- Started: 2026-09-29
- Definition of Done: an Approved plan means the requirements, smallest surface, ordered steps and test scope are grounded in the actual code and sufficient for a surgical implementation of GitHub issue #30 (add opt-in bounded concurrent dispatch to live `eval`/`ask` without changing any freeze, checkpoint or result guarantee).
- Operational envelope: a small stdlib-only Python CLI run by one developer on a laptop. Grade against the stated requirements and commensurate complexity. Do NOT demand enterprise machinery (distributed locks, journals, resumable state stores, async runtimes, rate-limit frameworks, multi-tenant threat models). Challenge any unneeded machinery in the plan itself. No new test frameworks.
- This is a REVIEW turn: read only, append findings here, do not edit the target repo.

### Questions (answer each, cite `file:line`)
1. Are the plan's Observed-problem claims true? Verify cli.py:190-206 (sequential loop, `answer-{len(completed):04d}` naming), client.py:100-101 and openrouter.py:73-76 (unlocked counter updates), and the ordered mocks.
2. Is one `threading.Lock` around the counter updates sufficient for thread safety of `JevClient`/`OpenRouterClient`? Is any other shared mutable state touched from the worker (e.g. `urllib` opener, `time.sleep` retry path, `write_results`)?
3. Does the plan keep N=1 byte-identical to today? Check the `--repeat` checkpoint suffix logic (`-r{attempt}`) and `drifts`/`completed` ordering when the per-record body moves into a function.
4. Failure semantics: does step 4 (stop dispatch on first error, let in-flight finish and checkpoint, re-raise, no `answers.json`) correctly preserve the GH-6 guarantee that every paid completed answer is on disk? Is anything missing about `ThreadPoolExecutor` cancellation behaviour?
5. Is refusing `--concurrency > 1` for mock/fixture/replay the right call versus a deterministic mock path? Does it leave the offline acceptance test viable (the plan uses a patched thread-safe fake live client)? Is that patch approach consistent with the existing tests' network-blocking patches?
6. Is the plan surgical and DRY? Does it extend the existing loop rather than add a second system? Flag any overbuilding, and any missing requirement from issue #30 (scope: opt-in bounded concurrency, keep checkpoints and ordered results and retry, stable per-record identity, preserve every freeze guarantee, tests network-free).
7. Is the test scope commensurate (existing file, no new framework), and does it include a red control that would actually fail if results came back in completion order rather than input order?

## Ground rules
1. This file is the single source of truth. The agents never share memory — read the whole file.
2. Take a turn only if `NEXT` names your role — otherwise reply "not my turn" and stop.
3. One turn = one block appended at the very bottom, above the marker. Never edit earlier turns.
4. Stay tight — findings are bullets, not essays. Grade every finding.
5. **The Reviewer never edits the artifact.** It proposes graded findings; the Producer implements.
6. The relay ends on **Approved** (Reviewer only). End each turn by committing just this file; no push.

## Log

<!-- ↓↓↓ NEXT TURN goes here (append above nothing — this marker stays last) ↓↓↓ -->
