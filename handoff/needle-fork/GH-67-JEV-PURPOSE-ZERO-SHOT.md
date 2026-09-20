---
gh_issue: 67
source: https://github.com/HiQS-Labs/Needle-fork/issues/67
title: "GH-67: TypeSafe Jev zero-shot rerun of the #31 40-record purpose/area holdout"
status: in-progress
created: 2026-09-18
updated: 2026-09-18
owner: Claude Code (start-task)
doc_type: feedback
goal: score Jev jev-1.13.0 zero-shot on the frozen #31 holdout with the #547 metrics and report the comparison, without tuning on the holdout or sending non-public text
related: [31, 29, 57, 58]
effort: 1
complexity: 1
risk: 1
phases: 1
---

# GH-67 — Jev zero-shot rerun of the #31 purpose/area holdout

## Status

| What was just completed | What's next |
|---|---|
| Plan approved r3 (agy). Runner frozen at `453cae1`, one live run: **purpose 37/40 (92.5%, mF1 0.675) vs ModernBERT 23/40; area 32/38 (84.2%, mF1 0.696) vs TF-IDF 12/38**; every prediction at confidence ≥ 0.8 correct. [Receipt](../../TESTS-RESULTS/2026-09-18-jev-purpose-zero-shot/SUMMARY.md). | Final relay QA on the diff + receipt, non-slow tests + pdda, CHANGELOG, push to `main`, post to #67 / XYZ-forge #709. Any follow-up (fresh human-adjudicated sample, confidence gate) is a new issue. |

## Observed problem

[#31](https://github.com/HiQS-Labs/Needle-fork/issues/31) ended with two weak classifiers on the operator-calibrated eight-purpose task (ModernBERT 23/40, TF-IDF 20/40) and no deployable area or rejection policy. The operator asked (2026-09-18, [XYZ-forge #709](https://github.com/HiQS-Labs/XYZ-forge/issues/709)) whether a zero-shot decision model, TypeSafe Jev, reaches the same bar with no training. Nothing in this repo can answer that today.

## Recon (base `f965a53`, clone `needle-fork-gh67-jev-purpose`)

- Scoring source of truth: XYZ-forge `TESTS-RESULTS/2026-09-10+GH-547-calibrated/run.py` at `430f432`. Text template `texts()`: `'Project: '+repo+'\nTitle: '+title+'\nDescription: '+description`. Metrics `metrics()`: `correct`, `raw_accuracy`, `macro_f1` (sklearn, `labels=` union of class list and truth, `average='macro'`, `zero_division=0`), confusion over that universe; area scored on records whose truth is non-null (38).
- Baselines from `results.json`: purpose tfidf 20/40 mF1 0.430, modernbert 23/40 mF1 0.370; area tfidf 12/38 mF1 0.206, modernbert 10/38 mF1 0.221. Majority purpose 17/40, area 4/38.
- Local data: `~/.cache/xyz-modernbert-calibrated/` — `holdout.json` (40 records: `id, repo, number, title, description, description_truncated, split, source_type, created_at`), `holdout-labels.json` (40: `purpose_primary`, `area_primary`, `confidence`, …), `taxonomy.md`. `input-hashes.json` in the #547 dir carries sha256 for `holdout-labels.json` (`70aa61d4…`) and `taxonomy.md` (`2a373c3b…`); `holdout.json` itself is not in that manifest, so this plan pins it too: sha256 `24995fe28edf56d3c77be41d9e0baec958006f987889efc51369fa77e5eedf26` (the operator's local snapshot as verified on 2026-09-18). All three hashes are constants in the script (QA r1).
- Repos in the holdout, all `PUBLIC` on 2026-09-18: XYZ-forge 22, rebalanceOS 5, Needle-fork 5, AEGIS-Sleuth-Slackbot 2, Orion-fork 2, XYZ-code-RAG 2, Model-catalog 2.
- Jev contract (docs, verified with one live call): `POST https://api.typesafe.ai/v1/systemone`, bearer key, body `{state, model, questions}`; Choice answer has `choice`, `probabilities`, `confidence`; response `model` is the versioned ID; `usage.input_tokens`. Limits: 32k state + longest question; max description here is 1,800 chars, so no truncation needed. Jaggedness relevant here: literal reading and indirection — the criteria must carry the taxonomy's boundary sentences, not just the label names.
- Existing conventions: research scripts live in `spike/<topic>/`, tests in `tests/test_*.py`, HTTP via `urllib.request` (`spike/coding_core/context_probe.py`), results in `TESTS-RESULTS/<date>-<slug>/`. No `requests` dependency in `requirements.txt`.

## Requirements

1. Score `jev-1.13.0` zero-shot on the 40 holdout records with one request per record carrying two Choice questions (`purpose`, `area`); criteria text = the **full** taxonomy v3 bullet for each label including its boundary sentences (e.g. "A comparison plan is this, not planning just because it says plan"), not a first sentence (QA r1). `ci_cd`, `skills` and `ui` carry no definition in the taxonomy beyond "operator confirmed"; their one-line glosses are the script's and are recorded in the results provenance. Area keeps the 12-class forced choice with no `none` option and is scored on the 38 non-null rows, the same denominator as #547 (QA r1). State = the `texts()` string.
2. Same metrics as #547 for both axes — `correct`, `raw_accuracy`, `macro_f1` over the union of taxonomy classes and truth labels with zero-division → 0, confusion — computed in plain Python as `spike/coding_core/shortlist_eval.py` does; **no sklearn** (QA r1). Plus per-record `confidence` and a table of accuracy by confidence bucket (`<0.5`, `0.5–0.8`, `≥0.8`).
3. Freeze checks before the first request: sha256 of `holdout.json`, `holdout-labels.json` and `taxonomy.md` must equal the pinned constants (so the bytes sent are exactly the verified public snapshot — QA r1); every record's `repo` must be `PUBLIC` via `gh repo view --json visibility` (skipped records are reported, never sent).
4. Provenance: pinned model ID from each response, `usage.input_tokens` sum, sha256 of every request and response body, run UTC, script sha256. Published files contain aggregates, per-record predictions keyed by `id`, and hashes — no titles or descriptions.
5. No tuning on the holdout: the criteria strings are committed before the run; any wording change after a holdout request invalidates the run and requires a new results directory. `holdout-labels.json` is hashed as bytes before the run and parsed only after the last response is in (QA r1). There is no validation mode; wording is frozen as committed.

## Non-goals

- Training, fine-tuning, prompt iteration on the holdout, secondary labels, or a rejection policy.
- Any change to the `needle` runtime, the 44-label Oracle, or the #62/#59 gates.
- A TypeSafe SDK dependency; `urllib.request` is enough.
- Re-collecting or expanding the holdout.

## Smallest affected surface

- New: `spike/work_classification/jev_zero_shot.py` (~200 lines: freeze check against three hardcoded hashes, visibility check, request builder, plain-Python scorer, writer; `--dry-run` runs the checks and builds requests without sending). No validation mode (QA r1).
- New: `tests/test_jev_zero_shot.py` (scorer math on a fixture: one wrong purpose, one null area, and one class with zero support and zero predictions → expected counts, macro-F1 with that class scoring 0; empty input rejected; the `texts()` template and the freeze check's mismatch path asserted).
- New: `TESTS-RESULTS/2026-09-18-jev-purpose-zero-shot/{SUMMARY.md,results.json,requests.jsonl (hashes only)}`.
- Touched: `ROADMAP.md` pointer (promotion), `CHANGELOG.md` at iteration end.
- Nothing else. No existing writer is extended because no existing subsystem scores work-purpose in this repo; #547's `run.py` is in XYZ-forge and stays there.

## Dependencies and risks

- Key: the operator's local secrets file, read at run time from `TYPESAFE_API_KEY` or `--key-file`; never logged. Risk: 429 under dynamic limits → retry with backoff honoring `retry-after`, max 5 attempts, then abort the run (partial results are not published).
- `gh` must be authenticated for the visibility check; if unavailable the run refuses.
- Rollback: delete the results directory and the two new files; nothing else changes.

## Ordered implementation

1. Write `jev_zero_shot.py` with the criteria dict copied from `taxonomy.md`; commit it **before** any holdout call (freeze).
2. Write `tests/test_jev_zero_shot.py`; run `python -m pytest tests/test_jev_zero_shot.py -q` → green.
3. `--dry-run`: freeze hashes match, 40/40 repos PUBLIC, 40 request bodies built, token estimate printed.
4. Live run once: 40 requests, results written, `usage.input_tokens` summed.
5. Write `SUMMARY.md`: comparison table (majority / tfidf / modernbert / jev for both axes), confidence buckets, caveats (model-annotated labels, n=40, not unseen evidence, no promotion), cost.
6. Run `python -m pytest tests -q -m "not slow"` and `utils/pdda/pdda.sh run`; update `CHANGELOG.md`; commit; push to `origin/main` per the 2026-09-12 operator branch policy; post the summary to #67 and cross-link on XYZ-forge #709.

## Acceptance checks

- `pytest tests/test_jev_zero_shot.py` fails if the scorer miscounts the fixture or accepts an empty list (red control: mutate one expected count in the fixture and confirm the test fails, then restore).
- `--dry-run` exits non-zero on a hash mismatch (red control: copy the cache to a temp dir, tamper `taxonomy.md`, run `--dry-run --cache-dir <temp>`; the hashes are hardcoded constants, there is no `--hashes` flag).
- `results.json` has 40 purpose predictions, 38 area truths counted, a `model` value of `jev-1.13.0` on every response, and request/response hash lists of length 40.
