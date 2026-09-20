# Handoff — evidence and artifacts from the HiQS Jev experiments (2026-09-18 → 2026-09-20)

This directory is the raw material for issue #1 of this repo. It is a snapshot, not a
dependency: everything here also lives at a pinned commit in its source repo, and the source
stays canonical. Read `../` issue #1 first; it is the specification. `MANIFEST.json` lists the
sha256 of every file in this directory.

## What is here

| Path | Origin (pinned) | What it is |
|---|---|---|
| `needle-fork/spike/work_classification/jev_zero_shot.py` | HiQS-Labs/Needle-fork `f7c7047` | The #67 runner: stdlib `urllib` client, pinned model, frozen `QUESTIONS` (purpose + area Choice pair, taxonomy v3 criteria), freeze checks, per-repo `PUBLIC` gate, #547-identical `texts()` and `metrics()`, confidence buckets. **Port this.** |
| `needle-fork/spike/work_classification/jev_fresh_eval.py` | same | The #69 runner: reuses `jev_zero_shot` unchanged; adds inputs, visibility re-check and the pre-registered gate evaluator. **Port the gate.** |
| `needle-fork/spike/work_classification/fresh_sample.py` | same | Keyword-blind, seeded sampler of public HiQS-Labs issues/PRs with a per-repo cap and a manifest. |
| `needle-fork/tests/test_jev_zero_shot.py` | same | Scorer tests: counts, macro-F1 incl. zero-support class, null truth, empty/misaligned refusal, freeze mismatch, forced-choice question shape, visibility runner. |
| `needle-fork/GH-67-JEV-PURPOSE-ZERO-SHOT.md`, `GH-69-JEV-FRESH-SAMPLE.md` | same | The two plan/capture docs with recon, requirements, gates and outcomes. |
| `needle-fork/TESTS-RESULTS/2026-09-18-jev-purpose-zero-shot/` | same | #67 receipt: `SUMMARY.md`, `results.json` (metrics, confusion, per-id predictions + confidence, provenance hashes), `requests.jsonl` (request/response sha256 per id). |
| `needle-fork/TESTS-RESULTS/2026-09-19-jev-fresh-sample/` | same | #69 receipt: `SUMMARY.md`, `manifest.json` (pool, seed, cap, exclusions, `quiz_sha256`, annotator commitments), `answers/` (Claude blind, Codex Astra XH blind, agreed rows, final consensus with agy's reasons), `jev/results.json` + `requests.jsonl`. |
| `xyz-forge/TESTS-RESULTS/2026-09-18+GH-712/` | HiQS-Labs/XYZ-forge PR #714 (`6f9983d5`) | ATE triage replay receipt: `SUMMARY.md`, benchmark and error-log `summary.json` + `rows.jsonl` (verdicts, confidence, model, hashes; no stderr text). |
| `xyz-forge/PROJECT/GH-712-JEV-ATE-TRIAGE.md` | same | The ATE plan: question design (status/severity/category Choices, `env_missing`, 1,500-char tails, `expects_edits` rule), the gate, and why Phase 3 was not started. |
| `xyz-forge/relay-system/jev-research-agy-PROMPT.md` | XYZ-forge #709 | The deeper-research brief for agy on Jev fit, state design, confidence, experiment critique. |

## What is deliberately NOT here

- **`quiz.jsonl`, `QUIZ.md`, `ADJUDICATION.md`, the agy adjudication relay thread** (they contain issue titles/descriptions). This repo stores no source text by policy; fetch them from Needle-fork `f7c7047` under `TESTS-RESULTS/2026-09-19-jev-fresh-sample/` when a live example needs the state, and verify `quiz_sha256` from `manifest.json` (`cb9e9616…`).
- **The #31 holdout records and labels** (`~/.cache/xyz-modernbert-calibrated/`). The labels were never published (Needle-fork #31 kept them local); the #67 `results.json` carries the confusion matrix and per-id predictions, which is enough to reproduce the metrics without them.
- **`utils/py/jev_triage.py` from XYZ-forge.** XYZ-forge is AGPL-3.0 and this repo is GPL-3.0; the file was not copied. Re-implement the ATE triage set from `xyz-forge/PROJECT/GH-712-JEV-ATE-TRIAGE.md` §Requirements, or ask the copyright holder (HiQS-Labs) to relicense that one file.
- **Any API key or live response body.** Only hashes of responses are stored.

## Licences

- `needle-fork/**` code is Apache-2.0 (HiQS-Labs/Needle-fork). Keep the header and record the origin in a `NOTICE` at the repo root when porting.
- Receipts and plan docs are HiQS-Labs' own material, included by the operator.

## Reproducing the numbers through the mock path

- **#67 (purpose 37/40, area 32/38):** `results.json → axes.<axis>.metrics.confusion` and `confusion_labels` are sufficient to recompute `correct`, `raw_accuracy` and `macro_f1`; a test can assert the harness's `metrics()` agrees with the stored values from the confusion matrix alone.
- **#69 (purpose 88/100, gate 73/75 at ≥ 0.8, coverage 75%):** `answers/consensus.jsonl` (labels by id; `uncertain` → excluded) + `jev/results.json → predictions[]` (choice + confidence by id) reproduce every metric and the gate with no text. Build the canned `MockClient` responses from `predictions[]` (probabilities were not retained; set the chosen option to the recorded confidence and leave the rest absent — the harness must not require probabilities for scoring).
- **#712:** `benchmark/rows.jsonl` has `label`, `tier1`, `status/severity/category`, `confidence` per row — recompute FN/FP/agreement and `fn_zero_threshold` (0.48) from `confidence.status` and `status`.

## Cross-references

Needle-fork #67, #69, #72 (the spec this issue #1 was copied from), #29 (taxonomy), #64 (the vendored agy shim model-list defect hit during #69); XYZ-forge #709 (umbrella), #712 / PR #714 (ATE triage); TypeSafe docs https://docs.typesafe.ai/llms.txt.
