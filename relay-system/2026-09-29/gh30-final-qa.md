# RELAY · GH-30 final QA: bounded concurrent dispatch
<!--
  Single source of truth for this two-agent relay. Read the ENTIRE file before acting.
  Scaffolded by relay-automation/new-relay.sh on 2026-09-29.
-->

NEXT: Producer
STATUS: Open
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


### Reviewer · Round 1

VERDICT: FAIL
Basis: The production implementation follows the Approved plan's observed-failure semantics, but two schedule assumptions make the new concurrency acceptance tests flaky. Correct those tests and obtain fresh disposable-clone evidence before approval.

swept file: yes

Read the entire plan and all of `jev/cli.py`, `jev/client.py`, `jev/openrouter.py`, `tests/test_jev_harness.py`, and `README.md`, including pre-existing code; traced answer projection, drift and the results writer. No additional pre-existing runtime defect identified in this sweep. Graph tools were unavailable, so project/generation and coverage checks were unavailable; evidence is direct source inspection. No Git command, suite, executable fixture, live request, or source modification was performed. Only an in-memory probe of the seeded dispatch statements was executed.

- [Should] **F1 — Fix the ordering test's schedule assumption (question 5).** `tests/test_jev_harness.py:775-780` releases s3, waits for its fake call to finish, then releases s2/s1, but s4–s6 are ungated. The production loop may correctly replenish immediately after s3; s4 can finish before the controller releases s2. Thus `seen["order"][:3] == ["s3", "s2", "s1"]` rejects a correct implementation. Also, fake-call completion at line 737 precedes checkpoint writing and Future completion, so this event alone does not establish the assembler's observed completion order. Synchronize the actual checkpoint/Future boundary for the reversal control; permit valid interleaving of replenished records (or gate those records too), while retaining input-order and bounded-overlap assertions. Propagate controller-thread assertion failures to the test thread rather than relying on background tracebacks (`drive`, lines 758-765).
  Observed input: six records s1–s6, N=3, first three gated; s3 finishes, the controller is delayed before releasing s2, and the dispatcher starts s4. The source-extracted dispatcher produced prefix `['s3', 's4', 's2']` with correctly ordered assembled results.
  Affected scope: the normal-run concurrency test and its controller synchronization; no production dispatch behavior change requested.
  Falsifier: this legal interleaving passes the corrected test, while a completion-order assembler and a serial dispatcher each fail in a disposable clone.
  Probe command: `export PYTHONDONTWRITEBYTECODE=1 TMPDIR="$PWD/.relay-scratch/tmp"; python3 "$TMPDIR/dispatch_probe.py"` (exit 0). The scratch script AST-extracted the unchanged top-level statements at `jev/cli.py:212-243`; injected only `send`, six string records, and concurrency=3; used real stdlib futures. Its controller waited for s1/s2/s3 entry, released s3, waited for s3 and s4 completion, then released s2 and s1. Decisive output: `normal completion prefix: ['s3', 's4', 's2']`; `test line 780 assertion: False`; `assembled input order: ['s1', 's2', 's3', 's4', 's5', 's6']`. This measures the scheduling assumption, not a run of the test suite.

- [Should] **F2 — Signal the actual failing repeat before releasing held records (question 5).** `tests/test_jev_harness.py:737` sets the same finished event after every attempt. With repeat=2, `finished("s3").wait(5)` at line 794 can return after the successful first call, contrary to its comment. If the worker pauses while checkpointing that answer, the controller releases s1/s2; their records may finish and legitimately dispatch s4 before s3's second call fails. Use an attempt-specific failure/Future-observation handshake before releasing s1/s2, preserving the earlier-repeat checkpoint check. Do not fix this by restricting valid production replenishment.
  Observed input: existing `fail=("s3", 2)`, repeat=2, s1/s2 held; finished(s3) is already set by call 1. In the same source-extracted probe, holding s3's failure until s4 entered, while releasing s1/s2, yielded `failure: second repeat failed` and `s4 started before s3 second-repeat failure: True` (same command, exit 0). This is the schedule the existing controller mistakenly allows.
  Affected scope: failure-test synchronization and controller error propagation, not the runtime failure contract.
  Falsifier: delay s3 between its successful first attempt and second-attempt failure; the corrected controller must keep s1/s2 held until failure observation. The correct implementation passes; eager submission or replenishment after an observed failure fails in the disposable clone.

- [Pass] **Question 1 — worker, order and checkpoint boundaries.** `jev/cli.py:194-210` checkpoints each successful attempt under eligible-position names, preserves the first answer for scoring, and uses unchanged first/no-suffix then -r2/-r3 naming. Inline N=1 and indexed N>1 results feed ordered completion/drift assembly (`212-245`). Outstanding records are bounded by initial N submissions and one replacement per returned completion (`219-237`); on observed errors, cancellation removes not-started work and the loop/context waits for running records before raising (`238-243`). Aggregates follow that raise (`248,303`). No additional dispatcher path discarding a successfully written checkpoint found. This does not promise retention when response validation or the checkpoint write itself fails (`198-209`).

- [Pass] **Question 2 — first observed error, not chronological first.** Every Future in the returned `done` set is inspected before replenishment (`jev/cli.py:228-237`); `failure = failure or error` retains the first encountered ordinary exception during later draining. Two failures in one unordered set can select either exception, regardless of wall-clock failure order. A Future finishing after the wait snapshot remains pending and is examined on a later iteration. This matches the plan QA's explicit “entire returned completion set” interpretation (`relay-system/2026-09-29/gh30-plan-qa.md`, Round 2 question 4); it is not an atomic promise to halt at the instant any worker fails. No additional chronological-error machinery requested.

- [Pass] **Question 3 — accounting transaction and constructor coverage.** `jev/client.py:80,102-105,146` initializes both TypeSafe constructors and locks token/model updates. `jev/openrouter.py:48,73-80,119` protects cumulative-cost validation and all updates together; rejected cumulative overflow precedes any update. Requests, openers and retry state remain per-call locals (`jev/client.py:110-137`, `jev/openrouter.py:85-112`). Report reads occur after workers exit (`jev/cli.py:249-259`). No further lock needed for these paths.

- [Pass] **Question 4 — guards and serial structure.** Bounds/type checks and concurrent-mock refusal occur at `jev/cli.py:128-138`, before output reservation at 193. Fixture setup supplies mocks at 112; replay without mocks is refused at 137. N=1 executes the shared worker inline (`213-215`); ask still constructs one record (`118`). Freeze/visibility/label-commitment checks remain before dispatch (`139-189`); labels are opened after finalized answers (`280-287`). Exact pre-change byte parity remains unverified below.

- [Pass] **Questions 5–6 — bounded implementation and useful assertions, with F1/F2 outstanding.** Source uses stdlib executor/locks and one shared record body (`jev/cli.py:6,194-243`), not another dispatch subsystem. Network/process blockers remain at `tests/test_jev_harness.py:37-43`. The new tests assert ordered IDs, names, peak=3, retained repeat checkpoints, absent aggregates, bounds and accounting (`778-856`). Accounting uses the inherited production methods and a held-lock check (`831-855`); its 0.3-second join is timing-based evidence, not a deterministic guarantee that an unlocked mutant has actually run. No sleep was added to the controlled dispatch tests. Strengthen synchronization where F1/F2 identify concrete invalid assumptions.

- [Nit] **Question 6 — qualify README timing claims.** `README.md:18` says “if a request fails, no new records start”; describe stopping dispatch once failure is observed, consistent with the returned-set semantics above. At `README.md:76`, “before the next request” should mean the next repeat for that record under concurrency. The range/default/live-only claims at `18,79` match `jev/cli.py:128-138,317`.

- [Unverified — needs clone run] The Producer's 84-test, baseline-byte-parity and mutation-red claims are summarized in the plan's Implementation evidence, but raw run receipts/baseline outputs are not present in this relay workspace. No suite or mutation was run here. Have the harness/Producer run the corrected tests and red controls in a disposable full clone, including the delayed-controller and delayed-second-repeat schedules above, then record commands, statuses and decisive output. Byte parity must include all eight files for denied/A/B with repeat=3. With Git prohibited and no seeded diff, the exact `445ef5e..224ef81` changed-file inventory and absence of stray changes are also unverified; source review establishes the visible design's scope, not that diff claim.

Handing off to Producer (claude-a) — disposition F1/F2, correct the test synchronization, and provide disposable-clone evidence for round 2; go to the Producer window and say “take your turn.”

### Producer · Round 1

Dispositions:
- F1 — Implemented. The ordering test now gates all six records and fixes completion order by waiting for the replacement record to start (a replacement starts only after the dispatcher observed a completion), so the order s3,s2,s1,s6,s5,s4 is deterministic and a legal s4-before-s2 interleaving cannot occur. Input-order and peak=3 assertions kept. Controller assertion failures now propagate to the test thread (`drive`).
- F2 — Implemented. The fake signals a `failed` event on the exact failing call; the controller waits for `failed("s3")` (the second repeat) before releasing s1/s2, so a successful first repeat can no longer satisfy the wait.
- Nit (README timing) — Implemented: "once a failure is observed no new records start"; "before that record's next request".
- Unverified item — addressed: disposable-clone receipts (84 tests OK, 8-file diff inventory, byte parity at default and N=3, six mutation controls killed, 30-run stress 0 failures) are recorded in the plan under "Final-QA round 1 receipts". Code under review is unchanged except tests and README.

Requesting Round 2 of the commit that follows this block; run `git diff 445ef5e..HEAD` for the current inventory.


### Reviewer · Round 2

VERDICT: FAIL
Basis: F1 and the README nit are addressed. F2 is only partially addressed: the new attempt-specific event still precedes Future completion and dispatcher observation, so the failure test can reject the correct implementation under a legal schedule. One test-only synchronization correction remains.

swept file: yes

Read the entire Approved plan and the full current cli.py, client.py, openrouter.py, test_jev_harness.py and README.md, including pre-existing code; inspected the projection, drift and writer seams. No additional pre-existing runtime defect identified. Graph tools were unavailable, so project/generation and coverage checks could not be performed; this is direct-source review. No Git, test suite, executable fixture, live request or source edit was performed. The narrow probe executed only AST-extracted dispatch statements with synthetic in-memory workers; scratch is not durable evidence.

- [Pass] **F1 closed; question 5 ordering/controller handling.** All six records are now gated, and replacements s4/s5/s6 cannot enter until the dispatcher consumes s3/s2/s1 respectively (tests/test_jev_harness.py:781-792). This establishes enough actual Future completion ordering to reject completion-order assembly. The final three fake-call exits are gated in sequence (793-798); their checkpoint/Future order is not guaranteed, but correctness no longer relies on it because the first three completions are already reversed. Controller assertions now propagate to the test thread (759-777), and input-order, checkpoint-name and peak=3 assertions remain (799-803).

- [Should] **F2 remains open — synchronize failure observation, not the impending raise (question 5).** The event at tests/test_jev_harness.py:731 is set before the exception at 732 and before the executor marks its Future failed. The controller at 812-814 can therefore release s1/s2 while s3 is paused at that boundary. Their Futures can complete first and legitimately cause replenishment at jev/cli.py:228-237. Line 817 then fails on a correct dispatcher. The successful-first-repeat ambiguity is fixed, but the required observation handshake is still missing. In the test, wrap the existing wait seam (or an equivalent dispatcher-observation boundary) and release s1/s2 only when a returned done set contains s3's failed Future. Keep the earlier-repeat checkpoint and no-aggregate assertions. Do not change production dispatch semantics or add sleeps.
  Observed input: existing six-state, N=3, repeat=2 failure case; pause s3 immediately after failed.set() at line 731 and before raise at 732; let the current controller release s1/s2. A source-extracted dispatcher probe started s4 and s5 before observing the synthetic failure, violating the test's line-817 condition.
  Affected scope: only failure-test synchronization in concurrent_run/controller; no runtime behavior change.
  Falsifier: with a forced pause at this boundary, the corrected controller keeps s1/s2 held until the failed Future is returned by wait; only s1/s2/s3 start, retained checkpoints remain, and serial/eager-submit/submit-after-observed-failure mutants still fail in a disposable clone.
  Probe command: `export PYTHONDONTWRITEBYTECODE=1 TMPDIR="$PWD/.relay-scratch/tmp"; python3 "$TMPDIR/failure_boundary_probe.py"`; exit 0. Script AST-extracted unchanged top-level dispatch statements jev/cli.py:212-243, used real stdlib futures and six string records, and modeled the scheduler pause with an event (no client, fixture or filesystem output). First ran the falsifying control: release held workers only after a returned completion set contains the error. Decisive output: `raised: synthetic failure; handshake: returned failure Future; started: ['s1', 's2', 's3']; line 817 condition: True`. Then modeled the current test's pre-raise signal, holding s3 until s4 enters: `raised: synthetic failure; handshake: failed event before raise; started: ['s1', 's2', 's3', 's4', 's5']; line 817 condition: False`. This measures the synchronization assumption, not a suite execution.
  Root cause: the test treats an impending worker exception as dispatcher-observed failure; Fix site: test controller's release handshake; Why not upstream/downstream: the production returned-set contract permits the measured replenishment, and weakening the final assertion would remove the intended regression control.

- [Pass] **Questions 1–2 — worker and dispatch.** Eligible-position naming, unchanged repeat suffixes, per-attempt checkpointing and first-answer scoring remain in jev/cli.py:194-210; inline serial and indexed concurrent assembly preserve record order (212-245). Initial submissions and replenishment bound outstanding records (219-237). Every returned done Future is examined before replenishment; ordinary exceptions preserve the first encountered error during draining (228-241), then re-raise precedes aggregates (242-248,303). Simultaneous errors in an unordered done set can select either; this is first observed, not chronological first. Futures completing after a wait snapshot remain pending for the next pass. No additional path losing a successfully written checkpoint found; response-validation or checkpoint-write failures remain outside that persistence guarantee.

- [Pass] **Question 3 — locks.** Both TypeSafe constructors initialize the lock (jev/client.py:80,146), and accounting is within it (102-105). OpenRouter cost validation and all counter/model updates share one critical section (jev/openrouter.py:73-80); its mock constructor calls the parent (119). Requests, openers and retry state are per-call (client.py:110-137; openrouter.py:85-112); aggregate counter reads follow executor completion (cli.py:249-259).

- [Pass] **Question 4 — serial structure and guards.** Bounds and concurrent-mock refusal precede output reservation (jev/cli.py:128-138,193); fixtures populate mock responses (112), and replay without mocks is refused (137-138). N=1 calls the shared worker inline (213-215); ask remains one record (118). Freeze, visibility and label commitments precede workers (139-189); label content is read after finalized answers (280-287). Exact baseline byte identity is reported by the Producer, not independently measured here.

- [Pass] **Question 6 and README nit closed.** The visible implementation uses one shared record worker, stdlib executor and one lock per client (jev/cli.py:194-243; jev/client.py:80,102; jev/openrouter.py:48,73), with no additional dispatch subsystem. README.md:18 now says "once a failure is observed" and :76 says "before that record's next request", matching the implementation. Bounds/default/live-only documentation at :18,79 matches cli.py:128-138,317. Exact changed-file inventory remains a reported clone result below.

- [Unverified — needs clone run] P = PROJECT/2-WORKING/GH-30-BOUNDED-CONCURRENCY.md. P:85-91 records the Producer's clone at 97f2cbb: 84 tests OK, eight-file inventory, eight-output byte parity, six killed mutants and 30 stress runs with no failures. These are recorded summaries, not independently inspected raw logs or rerun results. Ordinary stress does not force the event/raise gap reproduced above. After correcting F2, record the forced-gap result plus the final suite and relevant mutation results from the disposable clone. Network/process blockers remain in the test setup (tests/test_jev_harness.py:37-43); the accounting test exercises inherited production methods (845-874), though the held-lock negative control still relies on a bounded scheduling wait.

Handing off to Producer (claude-a) — finish the F2 observation handshake and record fresh disposable-clone evidence for round 3; go to the Producer window and say "take your turn." The harness owns the relay-file commit.

<!-- ↓↓↓ NEXT TURN goes here (append above nothing — this marker stays last) ↓↓↓ -->
