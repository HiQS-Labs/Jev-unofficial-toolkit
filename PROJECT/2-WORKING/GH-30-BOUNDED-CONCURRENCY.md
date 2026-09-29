---
gh_issue: 30
source: https://github.com/HiQS-Labs/Jev-unofficial-toolkit/issues/30
title: Bounded concurrent dispatch for eval/ask batches
status: Implemented — final QA pending
created: 2026-09-29
updated: 2026-09-29
owner: toolkit maintainer
goal: Let live `eval` send N records concurrently without changing any freeze, checkpoint, or result guarantee.
doc_type: feature
---

# GH-30 — bounded concurrent dispatch

Repo has no `releases.db`, `ROUTER.md`, `AGENTS.md` or `SOP.md`; PROJECT/1-INBOX → 2-WORKING is the only governance in use, and the base branch is `main`. No ledger installed for rating.

## Rating (no RELEASES ledger; recorded here)

`rated 35/20/50/60` (pri/sev/appeal/effort). Severity low: a speed feature, no data-loss defect. Appeal neutral (50, none supplied). Effort 60: one loop, one lock. Recurrence: unknown trend (no same-class issues in the repo).

## Observed problem (base 445ef5e)

- [jev/cli.py:190](../../jev/cli.py) sends records one at a time in a single `for` loop; `--repeat` nests inside it.
- Checkpoints are named `answer-{len(completed):04d}` (cli.py:204), which equals record position only because dispatch is sequential.
- `JevClient._answer` ([client.py:100-101](../../jev/client.py)) and `OpenRouterClient` (openrouter.py:73-76) mutate `input_tokens`, `output_tokens`, `cost`, `models_seen` with no lock.
- `MockClient`/`OpenRouterMockClient` consume an ordered response list; the order is only meaningful when dispatch is sequential.
- Retry with `Retry-After` already lives inside `ask()` per request; it needs no change.

## Requirements

1. `--concurrency N`, integer 1–8, default 1. Applies to `ask`/`eval` live runs.
2. At N=1 the code path, files and bytes are identical to today.
3. At N>1: results, `answers.json` and scoring keep input order; checkpoints are named by record position so names match N=1.
4. First failure stops new dispatch; in-flight requests finish and their checkpoints are written; the error is raised; no `answers.json`/`results.json`.
5. Client counters are correct under threads.
6. Every existing guard stays: manifest freeze, label commitment, new output dir, `--live`, `CI` refusal, visibility policy, text-free writer.

## Smallest surface

Extend the existing loop in `cli.run` and add one `threading.Lock` around the counter updates in the two `_answer`-style methods. No new module, queue, async runtime, or dependency (stdlib `concurrent.futures`).

## Non-goals

- Mock, fixture and replay runs: `--concurrency > 1` is refused there (ordered mocks are sequential by definition).
- Resume of a failed run into a used output directory. Position-named checkpoints leave that possible later; it is not built here.
- Provider idempotency keys: no documented support; not verified, not added.
- Any live request, benchmark or accuracy claim.
- A rate limiter beyond the existing per-request retry and the N ≤ 8 cap.

## Ordered implementation

1. One `threading.Lock` per client covers the whole accounting transaction in `JevClient._answer` and `OpenRouterClient` (including the cumulative-cost finiteness check at openrouter.py:71 with the updates at 73-76, inside one critical section). `MockClient.__init__` (client.py:139-142) bypasses `JevClient.__init__`, so it must create the lock too; `OpenRouterMockClient` inherits its parent constructor. Check: existing suite green; both mock paths still work.
2. Add `--concurrency` in `main`; in `run`, validate int 1–8 and refuse N>1 with mock/fixture/replay. Check: refusal tests (N=0, N=9, N=2 with mock).
3. Factor the per-record body (repeat loop, entry build, checkpoint write, returning `(entry, runs)`) into one local function; run it inline at N=1. "Record position" is the 1-based position in `sendable` (the eligible list, cli.py:150), not in the original input. Suffixes are unchanged: first answer none, then `-r2`, `-r3`; each successful attempt is checkpointed before the next call; only the first answer is scored; `completed` and `drifts` are assembled in `sendable` order. Check: N=1 checkpoint names and bytes, `answers.json` and `results.json` match a baseline produced by the unmodified code on the same inputs (run once in a disposable clone of main), including `[denied, public-A, public-B]` with `--repeat 3`.
4. Dispatch and failure at N>1: keep at most N outstanding record futures in a `ThreadPoolExecutor`; wait with `FIRST_COMPLETED`, inspect each completed future for an error before submitting the next record; on an observed failure stop submitting, `cancel()` futures not yet started, wait for running workers (a running record finishes its own repeats, each checkpointed), then re-raise; write neither aggregate file. Do not detect errors by waiting on futures in input order. Check: see the controlled-schedule test below.
5. Docs: one sentence each in README (replace "concurrent dispatch is not implemented") and the CLI section.

## Test scope (commensurate: existing harness, no new framework)

Add to [tests/test_jev_harness.py](../../tests/test_jev_harness.py) using its existing network-blocking patches and a thread-safe fake live client:

- Fake live client with event-controlled scheduling (`threading.Event`, no sleeps). Normal run, N=3, 6 records: peak active calls > 1 and <= 3; `answers.json` in input order; names `answer-0001..0006`.
- Red control: later records are released first so completion order is reversed; results must still be input order (an assembler that appends in completion order fails this).
- Failure schedule, N=3: records 1 and 2 held, record 3 fails; records 4-6 never start; after releasing 1 and 2 their checkpoints exist; neither `answers.json` nor `results.json` exists. Include one record whose first repeat completes before a later repeat fails and check that repeat's checkpoint. A serial or eager-submit variant must fail this test.
- Accounting: concurrent real `_answer` calls on `JevClient` and `OpenRouterClient` with canned responses give exact token/model totals, and a nonfinite cumulative cost is rejected without partial update.
- N=1 parity case from step 3 (skipped record, `--repeat 3`); refusal tests from step 2.
- Full `python3 -m unittest discover -s tests` once on the final commit.

## Risks / rollback

Default 1 keeps today's behavior; revert is one commit. Risk: a thread failing after paid completion — covered by per-record checkpoints written inside the worker.

## Plan QA (Approved, Codex round 2)

Round 1 (Codex, VERDICT FAIL, 3 Should + 3 Pass): F1 dispatch/failure algorithm and controlled-schedule test — Implemented (steps 3-4, tests). F2 lock covers the whole accounting transaction and `MockClient.__init__` — Implemented (step 1, accounting test). F3 numbering by `sendable` position and repeat/skip parity — Implemented (step 3, parity test). Round 2 review pending. Relay thread: `relay-system/2026-09-29/gh30-plan-qa.md`.

## Implementation evidence (2026-09-29)

- Code: `jev/cli.py` (`--concurrency`, `send()` worker, bounded dispatch), `jev/client.py` and `jev/openrouter.py` (one lock per client, also on `MockClient`), README.
- Full suite `python3 -m unittest discover -s tests`: 84 tests OK (79 existing + 5 new).
- Byte parity against the unmodified code (baseline from commit c3d9c36 code, same canned responses, inputs `[denied, pubA, pubB]`, `--repeat 3`): all 8 output files (6 checkpoints, `answers.json`, `results.json`) have identical SHA-256 at `--concurrency` default, and at `--concurrency 3`.
- Red controls, each run against a deliberately broken implementation: assembling results in completion order fails `test_concurrent_dispatch_is_bounded_ordered...`; submitting after a failure fails `test_concurrent_failure_stops_dispatch...`; removing the lock in `client.py` or in `openrouter.py` fails `test_client_accounting_is_exact_under_threads`. A lost-update count alone did not detect a removed lock (the GIL hides it), so that test also holds the lock and checks `_answer` blocks.
- Not run: any live request. No new live evidence or accuracy claim.
