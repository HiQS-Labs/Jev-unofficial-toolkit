---
gh_issue: 30
source: https://github.com/HiQS-Labs/Jev-unofficial-toolkit/issues/30
title: Bounded concurrent dispatch for eval/ask batches
status: Plan — awaiting plan QA
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

1. Lock the counter updates in `JevClient._answer` and `OpenRouterClient` answer handling. Check: existing suite still green.
2. Add `--concurrency` in `main`; in `run`, validate int 1–8 and refuse N>1 with mock/fixture/replay. Check: refusal tests (N=0, N=9, N=2 with mock).
3. Factor the per-record body (repeat loop, entry build, checkpoint write) into one local function; run it inline at N=1 or via `ThreadPoolExecutor(N)` at N>1; assemble `completed` and `drifts` in input order; name checkpoints by record position. Check: N=1 bytes equal to pre-change outputs on the existing checkpoint test.
4. Failure path: on first exception stop submitting, wait for in-flight, re-raise. Check: a fake client failing on record 3 of 6 at N=3 leaves no `answers.json`, every completed record has a checkpoint.
5. Docs: one sentence each in README (replace "concurrent dispatch is not implemented") and the CLI section.

## Test scope (commensurate: existing harness, no new framework)

Add to [tests/test_jev_harness.py](../../tests/test_jev_harness.py) using its existing network-blocking patches and a thread-safe fake live client:

- N=3 over 6 records: `answers.json` order equals input order; checkpoint names `answer-0001..0006`; counters equal the sum.
- Red control: an out-of-order fake (later records finish first) must still yield input-order results.
- N=1 result equals the pre-change checkpoint/answers output.
- Failure test from step 4; refusal tests from step 2.
- Full `python3 -m unittest discover -s tests` once on the final commit.

## Risks / rollback

Default 1 keeps today's behavior; revert is one commit. Risk: a thread failing after paid completion — covered by per-record checkpoints written inside the worker.

## Plan QA

Pending.
