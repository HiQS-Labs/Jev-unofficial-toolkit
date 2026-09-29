# RELAY · GH-30 plan QA: bounded concurrent dispatch
<!--
  Single source of truth for this two-agent relay. Read the ENTIRE file before acting.
  Scaffolded by relay-automation/new-relay.sh on 2026-09-29.
-->

NEXT: Producer
STATUS: Approved
ROUND: 2 / 3

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

### Reviewer · Round 1

VERDICT: FAIL
Basis: The proposed surface is appropriate, but dispatch/failure mechanics and two compatibility edges need explicit acceptance criteria before implementation. These are bounded plan corrections, not requests for a new subsystem.

swept file: yes

Read the whole plan, `jev/cli.py`, `jev/client.py`, `jev/openrouter.py`, and `tests/test_jev_harness.py`; also traced the results writer in `jev/guard.py`. No additional pre-existing defect found in that sweep beyond the shared-state hazards discussed below for the proposed concurrent use. Graph tools were unavailable; evidence is direct source inspection. `P` below means `PROJECT/2-WORKING/GH-30-BOUNDED-CONCURRENCY.md`.

- [Should] **F1 — Specify the bounded submission/failure algorithm and measure actual overlap (questions 4, 6, 7).** `P:54-55` specifies a pool and stopping submissions but leaves outstanding futures and exception observation unspecified. Say explicitly: keep at most N outstanding record futures, inspect completed futures for errors before replenishing, stop replenishing on an observed failure, cancel work that has not started, wait for running workers to finish checkpointing, and then re-raise without aggregate files. Do not wait on futures in input order to detect errors. Define whether an already-running record finishes its remaining repeats; keep each successful attempt checkpointed before the next call. A pool context manager waits but does not cancel queued work by default. Strengthen the six-record test with event-controlled overlap (peak active >1 and <=N), records 1/2 held while 3 fails, and an assertion that 4–6 never start in that controlled schedule. Assert both aggregate files absent and checkpoints for successful in-flight calls, including one completed repeat before a later repeat fails.
  Observed input: `P:55` uses failure on record 3 of 6 at N=3, but its asserted output does not detect eager submission of all six or a serial implementation; `jev/cli.py:192-204` currently checkpoints each successful repeat individually.
  Affected scope: N>1 scheduling and failure handling only; no change to provider retries or default serial failure behavior.
  Falsifier: the controlled schedule above starts only records 1–3, records successful in-flight attempts, emits neither aggregate, and a normal run demonstrates bounded overlap; an eager-submit or serial variant must fail these assertions.
  Probe: with `PYTHONDONTWRITEBYTECODE=1` and `TMPDIR="$PWD/.relay-scratch/tmp"`, ran `python3` importing `inspect`, `ThreadPoolExecutor`, and `Executor`, then `print(inspect.getsource(ThreadPoolExecutor.shutdown)); print(inspect.getsource(Executor.__exit__))`. Exit 0; decisive output: `def shutdown(self, wait=True, *, cancel_futures=False):` and `__exit__` calls `self.shutdown(wait=True)`. This was source inspection, not an executable fixture or suite run.

- [Should] **F2 — Complete the counter-lock scope and constructor coverage (question 2).** One lock per client is enough for the owned mutable accounting state, provided OpenRouter’s cumulative-cost finiteness check is inside the same critical section as all updates. Initialize the lock in TypeSafe `MockClient` too: its constructor bypasses `JevClient.__init__`, whereas `OpenRouterMockClient` calls its parent. Add these two details to step 1. Exercise the real `_answer` accounting in both backends with canned data; counters owned only by a fake client would not test the production lock.
  Observed input: `jev/openrouter.py:71` reads `self.cost` before the updates at 73–76; `jev/client.py:139-150` separately initializes mock counters and calls inherited `_answer`. `P:40,52` currently says only “around the counter updates.”
  Affected scope: each client’s accounting check/update transaction and all constructors reaching it, including serial mocks.
  Falsifier: both existing mock paths remain usable after lock introduction; concurrent real `_answer` calls preserve token/model totals and reject cumulative nonfinite cost without partially updating counters. A lock introduced only in the live TypeSafe constructor must fail the mock check.

- [Should] **F3 — Pin eligible-record numbering and repeat parity (question 3).** Define “record position” as the 1-based position in `sendable`, not in the original input. Preserve suffixes exactly: first answer has no suffix, then `-r2`, `-r3`; checkpoint inside each repeat, score only the first answer, and return per-record drift for ordered assembly. Extend parity coverage to a skipped first input and `--repeat 3`, plus a later-repeat failure. Compare checkpoint filenames and bytes, `answers.json`, and `results.json` against a pre-change baseline in the disposable clone; the current checkpoint test alone is insufficient.
  Observed input: `jev/cli.py:150` filters eligible records; `190-204` numbers by completed eligible records and uses `attempt + 1`. `tests/test_jev_harness.py:198-244` tests checkpoints without repeats or visibility filtering, yet `P:54,64` relies on that case for parity.
  Affected scope: naming and serialization compatibility in the factored record worker, at N=1 and N>1.
  Falsifier: input `[denied, public-A, public-B]` with repeat=3 yields `answer-0001{,-r2,-r3}.json` for A and `answer-0002{,-r2,-r3}.json` for B; N=1 bytes match the old implementation and N>1 ordered answers/drift retain the same identity mapping.

- [Pass] **Observed-problem claims and worker isolation (questions 1, 2).** The serial nested loops and completion-based names are present at `jev/cli.py:190-206`; unlocked counters at `jev/client.py:100-101` and `jev/openrouter.py:73-76`; ordered response consumption at `jev/client.py:147` and `jev/openrouter.py:122`. Requests, openers, retry counters and delays are per-call locals (`jev/client.py:107-134`, `jev/openrouter.py:82-109`). No shared opener or sleep state needs another lock. `write_results` uses local serialization and exclusive file creation (`jev/guard.py:81-86`), so distinct position/suffix paths suffice. Keep aggregate writes after worker completion (`jev/cli.py:209-220`).

- [Pass] **Offline boundary and surgical scope (questions 5, 6).** Refusing N>1 for ordered mocks/fixtures/replay is reasonable; no deterministic concurrent mock machinery is needed (`P:44`). The fake-live approach fits existing fail-closed network patches (`tests/test_jev_harness.py:34-40`) and live-path substitution (`tests/test_jev_harness.py:266-273`): patch the CLI client seam, visibility and dummy credentials, clear CI locally, retain socket/process blockers. One shared record body plus stdlib executor and per-client lock is commensurate (`P:40,54`). Keep freeze/visibility checks and output reservation before dispatch (`jev/cli.py:129-188`) and label reads after final answers (`jev/cli.py:241-250`). `ask` currently creates one record (`jev/cli.py:116-118`), so accepting N>1 need not make repeats concurrent.

- [Pass] **Ordering red control is directionally correct (question 7).** `P:63` explicitly forces later records to finish first while requiring input-order results. Use distinct IDs/answers and synchronization so the wrong completion-order assembler demonstrably fails; record that red result alongside the final clone suite result. The existing unittest file and full-suite command (`P:60-66`) are sufficient infrastructure.

- [Unverified — needs clone run] No suites or executable fixtures were run in this reviewer workspace. N=1 byte parity, concurrent accounting, failure/checkpoint controls and the complete existing suite remain implementation-time evidence. Source review establishes feasibility, not a passing implementation.

Handing off to Producer (claude-a) — disposition F1–F3 and revise the plan, then open round 2; go to the Producer window and say “take your turn.”

### Producer · Round 1

Dispositions:
- F1 — Implemented. Plan steps 3-4 now specify at most N outstanding futures, `FIRST_COMPLETED` error inspection, cancel-not-started, wait-for-running-then-reraise, no aggregates; tests use an event-controlled schedule (peak overlap, 4-6 never start, checkpoints for released 1-2, one completed repeat before a later repeat fails).
- F2 — Implemented. Step 1 puts the cost finiteness check and updates in one critical section and adds the lock to `MockClient.__init__`; new accounting test on the real `_answer` of both backends.
- F3 — Implemented. Step 3 defines position as 1-based in `sendable`, keeps suffixes unchanged, and adds a `[denied, public-A, public-B]` `--repeat 3` parity case plus a baseline byte comparison from unmodified code in a disposable clone.

Plan revised at commit below; requesting Round 2 review of the updated `PROJECT/2-WORKING/GH-30-BOUNDED-CONCURRENCY.md`.

### Reviewer · Round 2

VERDICT: PASS
Basis: F1–F3 are addressed. The plan now defines a bounded implementation and falsifiable acceptance criteria sufficient for GH-30 within the stated laptop CLI envelope. Approval is of the plan, not implementation test results.

swept file: yes

Read the whole revised plan, all of `jev/cli.py`, `jev/client.py`, `jev/openrouter.py`, `tests/test_jev_harness.py`, and the supporting `jev/guard.py`. No additional pre-existing defect found in this sweep. Graph tools were unavailable, so project/generation and index coverage could not be checked; evidence is direct source inspection. `P` below denotes `PROJECT/2-WORKING/GH-30-BOUNDED-CONCURRENCY.md`.

- [Pass] **Questions 1–2; F2 closed.** The observed serial loop, completion-based naming, unlocked accounting and ordered mocks remain at `jev/cli.py:190-206`, `jev/client.py:100-101,139-150`, and `jev/openrouter.py:71-76,114-125`. `P:52` now covers the complete accounting transaction, including cumulative-cost validation and the separate TypeSafe mock constructor; `P:65` exercises the real accounting methods. One lock per client suffices for this worker use: requests/openers/retry state are call-local (`jev/client.py:107-134`, `jev/openrouter.py:82-109`), and the results writer uses local serialization and exclusive creation (`jev/guard.py:81-86`). Distinct position/suffix filenames avoid worker collisions.
- [Pass] **Question 3; F3 closed.** `P:54` explicitly numbers eligible `sendable` records, preserves first-answer scoring, unchanged repeat suffixes, immediate per-attempt checkpoints, ordered answers/drifts, and inline N=1 execution. These match `jev/cli.py:150,190-206`. The skipped-first-record/repeat=3 baseline byte comparison covers the former parity gap; it must be performed with the same canned responses and inputs in the disposable clone.
- [Pass] **Question 4; F1 closed.** `P:55` now bounds outstanding futures to N, observes completion/errors before replenishing, cancels not-started futures, waits for running records to finish their checkpointed repeats, and re-raises without aggregates. Read “inspect each completed future” as inspecting the entire returned completion set before replenishment. This preserves the per-attempt checkpoint boundary at `jev/cli.py:193-204`; aggregate writes remain after successful dispatch (`jev/cli.py:209,264`). Explicit cancellation addresses the executor-context-manager limitation documented in Round 1.
- [Pass] **Questions 5–6.** Refusing concurrent ordered mocks/fixtures/replay (`P:44,53`) is appropriate. A thread-safe fake at the live-client seam is compatible with existing network/process blockers (`tests/test_jev_harness.py:34-40`) and live-path patches (`tests/test_jev_harness.py:266-273`). Keep those blockers active while patching visibility, credentials and CI locally. The plan uses one shared record body, stdlib futures, and per-client locks (`P:40,52-55`); no second dispatch system is needed. Existing preflight guards and output reservation stay before workers (`jev/cli.py:129-188`), labels after finalized answers (`jev/cli.py:241-248`). `ask` remains one record with serial repeats (`jev/cli.py:116-118`).
- [Pass] **Question 7.** `P:60-67` keeps tests in the existing unittest harness and specifies event-controlled overlap, bounded concurrency, reverse-completion ordering, failure without starting records 4–6, successful in-flight checkpoints, later-repeat failure, real accounting, parity, refusals, and the final suite. The completion-order assembler red control (`P:63`) can fail a wrong implementation; the serial/eager-submit controls (`P:64`) cover the scheduling gap. Record their actual red/green evidence with implementation QA.
- [Unverified — needs clone run] No suites, executable fixtures, or live requests were run here. Byte parity, concurrent accounting, ordering/failure red controls, and the final suite are still implementation-time checks required by `P:54,62-67`. This source review does not assert they passed.

Relay closed (Approved), no further review turn needed. Producer (claude-a) may proceed to implementation and disposable-clone verification; the harness owns the relay-file commit.

<!-- ↓↓↓ NEXT TURN goes here (append above nothing — this marker stays last) ↓↓↓ -->
