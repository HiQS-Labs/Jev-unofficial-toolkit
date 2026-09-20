# GH-69 — Jev zero-shot on a fresh 100-row sample with two-model-consensus labels

Run: 2026-09-19 · Model: `jev-1.13.0` on all 100 responses · Input tokens: 133,560 (~$0.006) · Criteria: the frozen `QUESTIONS` from `jev_zero_shot.py` at `453cae1`, unchanged (`questions_sha256` recorded) · Records sent: 100/100 (all repos `PUBLIC` at run time).

## Pre-registered gate — MET

| Purpose axis, rows with Jev confidence ≥ 0.8 | Required | Observed |
|---|---|---|
| Accuracy | ≥ 90% | **97.3%** (73/75) |
| Coverage of scored rows | ≥ 60% | **75%** (75/100) |

## Result

| Axis | Correct | Accuracy | Macro-F1 | Agrees with Claude | Agrees with Codex |
|---|---:|---:|---:|---:|---:|
| Purpose | 88/100 | 88.0% | 0.687 | 87/100 | 86/100 |
| Area (94 non-uncertain) | 60/94 | 63.8% | 0.639 | 59/100 | 62/100 |

For scale: the two frontier annotators agreed with each other on 91/100 purpose and 88/100 area rows. On purpose, Jev sits three to five rows below that inter-annotator ceiling; on area it is well below it.

## Confidence

| Axis | conf < 0.5 | 0.5 ≤ conf < 0.8 | conf ≥ 0.8 |
|---|---|---|---|
| Purpose | 2/5 | 13/20 | **73/75** |
| Area | 5/22 | 10/19 | 45/53 |

Purpose: the two high-confidence misses were `feature_enhancement`→`bug_fix` rows (PRs titled `fix(...)` whose primary objective the annotators judged as a capability change). Everything else Jev got wrong on purpose it was already unsure about. Area confidence is far less useful: 22 of 100 rows fell below 0.5.

## Where it misses

Purpose (12): `merge_closeout`→`documentation` ×2, `feature_enhancement`→`bug_fix` ×2, and one each of `maintenance`→`feature_enhancement`, `planning_design`→`documentation`, `planning_design`→`research_evaluation`, `bug_fix`→`research_evaluation`, `research_evaluation`→`documentation`, `bug_fix`→`feature_enhancement`. `documentation` is over-predicted (9 predicted, 5 true): Jev reads "docs:"-prefixed closeout and planning items as documentation. The three rarest classes (`merge_closeout` 1/3, `planning_design` 3/5, `maintenance` 4/5) carry most of the macro-F1 loss.

Area (34): `model_inference`→`documentation_policy` ×8 and →`core_harness` ×4 account for a third of the misses — Needle-fork research issues that *describe* model experiments in long governance-style text; `core_harness` is over-predicted (22 vs 14 true). `ingestion_sync` recall is 3/11. The area vocabulary is where the two annotators also diverged most (12 of their 20 disagreements), so part of this is the taxonomy, not the model.

## Labels: what they are and are not

- 80 rows: Claude and Codex Astra (extra-high) agreed blind on both axes. 20 rows: the two disagreed on at least one axis and **agy (gemini-3.8-flash-high)** adjudicated as a third blind model, siding with Codex on 12 calls and Claude on 9 (one row had both axes). Jev scored 73/80 on the agreed rows and 15/20 on the adjudicated rows.
- The operator delegated adjudication after finding the taxonomy terms hard to apply directly (recorded on #69). **No row was human-labelled.** This is a three-model consensus, not human gold; where Jev agrees with all three, all four can be wrong together. The honest reading of the headline is: *Jev, with no training, reproduces what a frontier-model annotation process would produce on ~9 of 10 rows for purpose, at roughly 1/1000 of the cost, and flags most of its own misses.*
- 6 area rows are `uncertain` in the consensus (auto-filed launchd health reports and a daemon plist fix) and are excluded from area scoring, not forced.
- Rows are unseen by any prior round (created ≥ 2026-09-10, after the #31 collection); this project's own Jev issues were excluded from the pool.

## Provenance

`manifest.json` (pool, seed, cap, exclusions, `quiz_sha256`, Claude's pre-run commitment `34960b1c…` verified on unsealing), `answers/{claude,codex-astra-xh,consensus}.jsonl`, `relay-system/2026-09-19/needle-69-agy-adjudication.md` (agy's calls), `jev/results.json` (metrics, confusion, per-id predictions, hashes), `jev/requests.jsonl`. No title or description text is stored under `jev/`.

## What this changes

The gate the operator pre-registered is met, so the next decision is **where to use it first**, not whether to keep testing it in the abstract. Recommended first use: auto-labelling purpose on intake for `/10days` and radar, with rows under 0.8 confidence routed to `uncertain` for a human. Area is not ready to act on unattended.
