# RELAY · GH-30 final QA: bounded concurrent dispatch
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
6. **Commit only the relay file** (`relay(gh30-final-qa): <role> r<N>`); no push. **Stop** and report one line.
7. **Hand off explicitly — EVERY turn, not just the first** (GH-268). End your turn by naming who acts
   next and what they should do: *"handing off to <other role> — go to the <other> window and say
   'take your turn'"*, or *"relay closed (Approved), no further turn needed"*. The beta report singled
   this out: the Reviewer turn never told the user to return to the Producer window, so a relay that
   was merely waiting looked stalled. A turn that ends without this line is not finished.

## Setup
- Artifact under review: the implementation of GitHub issue #30 in the TARGET repo (Jev-unofficial-toolkit) at commit 224ef81, against the Approved plan `PROJECT/2-WORKING/GH-30-BOUNDED-CONCURRENCY.md` (plan QA thread: `relay-system/2026-09-29/gh30-plan-qa.md`, Approved by codex round 2). Read the plan in full, then `git diff 445ef5e..224ef81 -- jev tests README.md` and the surrounding code: `jev/cli.py` (`run`), `jev/client.py`, `jev/openrouter.py`, `tests/test_jev_harness.py` (the five new tests: dispatch bounded/ordered, failure stops dispatch, serial/concurrent names by eligible position, bounds/mock refusal, accounting under threads).
- Reviewer: codex   ·   Producer: claude-a
- Started: 2026-09-29
- Definition of Done: `--concurrency N` (1-8, default 1) for live eval is implemented as the plan specifies; N=1 output is byte-identical to the pre-change code; results, checkpoint names and scoring keep input order; first failure stops new dispatch while running records finish and keep checkpoints, with no aggregate files; both clients account correctly under threads; every existing guard stands; tests are network-free and sized to the change.
- Operational envelope: a small stdlib-only Python CLI run by one developer on a laptop. Grade against the stated requirements and commensurate complexity; do NOT demand enterprise machinery (resume journals, async runtimes, rate-limit frameworks, multi-tenant threat models). Challenge unneeded machinery in the diff.
- This is a REVIEW turn: read only. You may run narrow read-only probes under `.relay-scratch/`; do not run the test suite in the relay worktree (a disposable-clone run is recorded below).
- Evidence already produced by the Producer (verify, do not just trust): full suite 84 tests OK at 224ef81 (79 existing + 5 new); byte parity vs unmodified code with inputs `[denied, pubA, pubB]` and `--repeat 3` at default concurrency and at `--concurrency 3` (identical SHA-256 for all 8 output files); red controls: completion-order assembly fails the ordering test, submit-after-failure fails the failure test, removing either lock fails the accounting test. No live request was made.

### Questions (answer each, cite `file:line`)
1. Does `send()` and the dispatch loop in `jev/cli.py` match plan steps 3-4 (position numbering in `sendable`, repeat suffixes, per-attempt checkpoint, bounded outstanding futures, error inspection before replenishment, cancel not-started, wait for running, re-raise, no aggregates)? Any path where a paid completed answer is lost?
2. Is there any case where the first failure is masked or a different exception than the first failure is raised, or where `failure` handling misses a done future?
3. Are the locks correct and complete in `jev/client.py` (including `MockClient.__init__`) and `jev/openrouter.py` (cost finiteness check inside the same critical section)?
4. Does N=1 remain behaviourally identical (including `ask`, mock, replay and fixture paths), and are the refusals for `--concurrency` outside 1-8 and above 1 with mocks/fixtures correct and placed before any output directory is reserved?
5. Do the new tests detect the actual failures (ordering, eager submission after failure, checkpoint retention, lock guarding) rather than merely pass? Any flaky timing (sleeps, races) that could fail on a slow machine?
6. Is the diff surgical and DRY with no duplicate subsystem, no unrequested machinery, no stray files? Are the README claims accurate to the code?

## Ground rules
1. This file is the single source of truth. The agents never share memory — read the whole file.
2. Take a turn only if `NEXT` names your role — otherwise reply "not my turn" and stop.
3. One turn = one block appended at the very bottom, above the marker. Never edit earlier turns.
4. Stay tight — findings are bullets, not essays. Grade every finding.
5. **The Reviewer never edits the artifact.** It proposes graded findings; the Producer implements.
6. The relay ends on **Approved** (Reviewer only). End each turn by committing just this file; no push.

## Log

<!-- ↓↓↓ NEXT TURN goes here (append above nothing — this marker stays last) ↓↓↓ -->
