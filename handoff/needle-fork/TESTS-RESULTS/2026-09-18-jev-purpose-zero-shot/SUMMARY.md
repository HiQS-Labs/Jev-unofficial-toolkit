# GH-67 — Jev zero-shot on the #31 purpose/area holdout

Run: 2026-09-18T23:34:47Z · Model: `jev-1.13.0` on all 40 responses · Input tokens: 55,579 (~$0.0023) · Script: `spike/work_classification/jev_zero_shot.py`, frozen at commit `453cae1` before the first request (`questions_sha256 21094cd4…`, `script_sha256 07405826…`) · Wall time 14 s · Records sent: 40/40 (all repos `PUBLIC` at run time, none skipped).

## Result

| Axis | Majority | TF-IDF + logistic (#547) | Frozen ModernBERT + logistic (#547) | **Jev zero-shot** |
|---|---:|---:|---:|---:|
| Purpose correct /40 | 17 | 20 (50.0%) | 23 (57.5%) | **37 (92.5%)** |
| Purpose macro-F1 | — | 0.430 | 0.370 | **0.675** |
| Area correct /38 labeled | 4 | 12 (31.6%) | 10 (26.3%) | **32 (84.2%)** |
| Area macro-F1 | — | 0.206 | 0.221 | **0.696** |

Same 40 records, same `Project / Title / Description` text, same metric definitions (`correct`, `raw_accuracy`, `macro_f1` over the union of taxonomy classes and truth labels with zero-division → 0; area scored on the 38 non-null truth rows). Baselines are copied from `TESTS-RESULTS/2026-09-10+GH-547-calibrated/results.json` in XYZ-forge at `430f432`.

## Confidence

| Axis | conf < 0.5 | 0.5 ≤ conf < 0.8 | conf ≥ 0.8 |
|---|---|---|---|
| Purpose | 2/3 correct | 5/7 | **30/30** |
| Area | 4/7 | 8/11 | **20/20** |

Every prediction at confidence ≥ 0.8 was correct on both axes; every miss sits below 0.8 (purpose misses at 0.46 / 0.53 / 0.59; area misses at 0.41–0.71). A confidence gate at 0.8 would answer 30/40 purpose and 20/38 area rows with zero errors and route the rest to the #29 contract's `uncertain` output. This is an observation on 40 rows, not a tuned threshold.

## Misses

Purpose (3): `holdout-002` truth `merge_closeout` → `feature_enhancement` (0.46); `holdout-008` `bug_fix` → `research_evaluation` (0.53); `holdout-013` `testing_validation` → `research_evaluation` (0.59). The one `merge_closeout` example in the holdout was missed, so that class scores 0 in macro-F1; `maintenance` has no holdout support and scores 0 by the zero-division rule, which is what holds macro-F1 at 0.675 despite 92.5% accuracy (same rule as #547).

Area (6): four of the ten `model_inference` rows went to `core_harness` ×2, `telemetry`, `ingestion_sync`; `holdout-011` `search_retrieval` → `ledger`; `holdout-037` `skills` → `core_harness`. `core_harness` is over-predicted (7 predicted, 4 true). The two null-truth area rows received `core_harness` and `telemetry` (forced choice, not scored — same denominator as #547).

## Caveats (carried from #31 and the plan)

- The holdout labels are **model-annotated** under the operator's calibration (a third model reviewer, blinded to training labels), not human gold. A zero-shot model agreeing with model annotators at 92.5% may partly reflect shared priors; the #547 classifiers were trained on labels from the same annotation protocol and still scored 50–57.5%, so the gap is not explained by that alone.
- n = 40. Purpose classes `maintenance` (0) and `merge_closeout` (1) are effectively untested; area classes `dependencies` and `integrations` have no support.
- This holdout was already observed by the #31 round. Nothing was tuned against it here (criteria committed before the first request, one run, labels parsed after the last response), but it is not "unseen evidence" for any follow-up model and must not be reused as such.
- Three area labels (`ci_cd`, `skills`, `ui`) have no definition in taxonomy v3; their one-line glosses are the script's (`area_glosses_by_script` in `results.json`). All three were classified correctly, but a taxonomy revision should own that wording.
- Zero-shot means no in-domain data was used; this does not establish that Jev generalises to other HiQS repos, private titles, or a fresh sample.

## What this does and does not change

- It answers the question in #67: on the frozen #31 holdout, Jev zero-shot clears the ModernBERT/TF-IDF bar by a wide margin on both axes, with confidence that separates its own errors.
- It does not promote anything. Per the plan, a better score is a signal to run a **fresh unseen sample** with human adjudication before any deployment decision; that is a new issue with its own gate. #62 and #59 are untouched.

Files: `results.json` (aggregates, confusion matrices, per-record predictions by `id`, provenance hashes), `requests.jsonl` (request/response sha256 per record). No titles or descriptions are stored.
