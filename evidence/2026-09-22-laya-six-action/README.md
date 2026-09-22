# Laya six-action comparison

Laya scored **15/100** (accuracy `0.15`, macro-F1 `0.11129932869063304`) on the exact frozen 100-row holdout used for the Jev next-action result in [issue #21](https://github.com/HiQS-Labs/Jev-unofficial-toolkit/issues/21) and the [SemIf comparison](../2026-09-22-semif-six-action/README.md). It did not exceed repeat-last (`22`), SemIf (`24`), majority (`26`), Needle's tuned scorer (`28`), Markov-1 (`37`), or phase-backoff (`42`). This is a repeated-sample engineering comparison, not evidence of statistical superiority or broader generalization.

## Decision

The result does not justify a Laya integration or replacement claim. It is a valid, reproducible measurement of Laya's recommended default English arm: all 100 rows routed to the root English checkpoint, all were scored on CPU/float32, no request-head or state tokens were truncated, no rows were skipped, and an independent verifier rebuilt the committed projections and aggregates from the frozen source-bearing inputs plus the untracked raw run.

| Arm | Correct / 100 |
|---|---:|
| Phase-backoff | 42 |
| Markov-1 | 37 |
| Needle tuned scorer | 28 |
| Majority | 26 |
| SemIf, Qwen3.5-4B direct MLX | 24 |
| Repeat-last | 22 |
| Jev original | 21 |
| Jev replay range | 18–21 |
| **Laya, root English checkpoint** | **15** |

Laya predicted `run_tests` 63 times, `read` 17, `search` 9, `run_command` 7, and `edit` 4; it never predicted `git`. Recall was `0/19` for `edit`, `6/29` for `read`, `2/26` for `run_command`, `5/7` for `run_tests`, and `2/19` for `search`. The holdout has no `git` examples, so git behavior is not measured. The strong `run_tests` skew is descriptive evidence for this arm, not a diagnosis of Laya generally.

## Frozen comparison

- Dataset: `nebius/SWE-rebench-openhands-trajectories`, revision `35455389ab51bf5e2306bfd436ef72d0f98bf882`, CC BY 4.0.
- Holdout: 100 q1 rows from two OpenHands trajectories; SHA-256 `f016551eda2f9912c2ab81887669281452777ac103737f6e9b092044064a8587`.
- Task: predict one of `edit`, `git`, `read`, `run_command`, `run_tests`, or `search` from the same rows, q1 state, prescriptive instruction, and option descriptions as #21/#22.
- Laya: commit `c7527708f9f5220c669d8aa385077cd28d04708a`, package `0.3.6`, recommended `Router`, default English arm.
- Model: `convaiinnovations/laya` root checkpoint at revision `1c5edc17a7acd8701df6fc341c0d179f1c62c982`; CPU; `torch.float32`; no tuning, shortlisting, alternate checkpoint, or context-budget change.
- Input/output hashes: `11bd8f2714ab73feb07e44b6da65785d8bd9a7999d1cb95581d7f0aeec610024` / `bdd42a8765ca225b4d43c4ef89e5d83e356b10c5d80808e12b5562e9975205b3`.

The semantic task/state/options are the same, but the requests are not byte-identical: Laya uses its own typed-question serializer, ModernBERT tokenizer/encoder, marker-token decision head, temperature buckets, and four-decimal probability rounding. The full instruction used `90/90` tokens and the six rendered options used `8/8`, `9/9`, `8/8`, `14/14`, `15/15`, and `8/8`. States ranged from `172` to `235` tokens (median `204`); all 100 fit, so the shipped 512-token context did not truncate this sample.

## Probability and confidence behavior

Laya's native probabilities are rounded independently to four decimals and are not calibrated here. Maximum option probability was below `0.5` on 38 rows (`12/38` correct), between `0.5` and `0.8` on 49 (`2/49` correct), and at least `0.8` on 13 (`1/13` correct).

Laya also returns normalized-entropy confidence, rounded to four decimals. Confidence was below `0.5` on 80 rows (`14/80` correct), between `0.5` and `0.8` on 18 (`1/18` correct), and at least `0.8` on two (`0/2` correct). Laya emitted its own load-time warning that one shipped temperature bucket is clamped and affected confidence should be treated as uncalibrated. This receipt makes no confidence-gating or calibration claim.

## Run envelope and verification

The final 100 forward passes reported `39.43955134099451s` summed elapsed time (`0.3840458539998508s` median, `0.3384893339971313s` minimum, `0.5494319159988663s` maximum). Model loading, input/snapshot/source validation, routing, and token preflight occurred outside those per-row timers. The environment was Darwin arm64, Python `3.11.15`, Laya `0.3.6`, torch `2.14.0`, Transformers `5.17.0`, safetensors `0.8.0`, Hugging Face Hub `1.32.0`, and NumPy `2.4.6`. Before importing Laya, the runner required the exact prepared-input SHA-256 and matched all eight top-level installed Laya Python files (`__init__`, `agent`, `common`, `email`, `lang`, `presets`, `router`, and `shortlist`) against commit `c752770…`.

Final QA invalidated two pre-QA candidates while closing provenance gates: the first lacked installed-source enforcement (raw SHA `8a3f42ab667d4851108672bcc6e58503ac759acf1b91a28e7119ad099397e737`), and the second omitted `lang.py` and checked the prepared-input hash only after inference (raw SHA `5e959db11532815ee89491cd4d7de7f0e85ab4aa3f0b53eef7bf6ac1b4b9b951`). Both are preserved outside Git. The final pass added only the complete pre-import request/source identity gates, used the same model/input/CPU arm, and produced byte-identical choices, probabilities, confidence, hashes, routes, and token fields across all 100 rows; only timings and source identity metadata differ. No tuning or result-dependent arm change occurred.

Seven offline Laya test-script entrypoints passed 343 checks before inference. The all-checkpoint `test_local_e2e.py` was not run because it requires English, multilingual, and typed-decisions checkpoints while this arm deliberately downloads only the root English checkpoint. A direct `pytest -q` attempt printed `34 passed, 0 failed` from `test_criteria.py` and then aborted collection because that script calls `sys.exit(0)` at import; the documented script entrypoints were therefore used individually. The receipt-local focused suite covers frozen inputs/baselines, head preservation, closed schemas, model identity, probability rounding and tie behavior, raw mutation reprojection, text-safety, and binding verification.

- [`results.json`](results.json) contains only allowlisted text-free predictions, hashes, timings, model identity, and aggregate metrics.
- [`provenance.json`](provenance.json) pins data, source, runner, input/output, runtime, and all five downloaded model artifacts.
- [`verification.json`](verification.json) independently rebuilds results/provenance from the frozen holdout, prepared input, and raw output, then binds the committed files by SHA-256.
- [`laya_next_action.py`](laya_next_action.py) prepares, runs, summarizes, and verifies the frozen arm; [`test_laya_evidence.py`](../../tests/test_laya_evidence.py) provides the red and green controls.

Raw third-party trajectory text, prepared input, model weights/cache, machine-local paths, the synthetic smoke output, and canonical raw Laya output are intentionally not committed. The retained per-row projection contains only indices, labels, rounded probabilities/confidence, hashes, token counts, and timings.

## Limitations

The sample is already known, contains only two trajectories, and has no git support. Its labels are the existing #21 labels, not a new independent human reference. No alternate Laya checkpoint, wording, richer-state, calibration, context-budget, fine-tuning, or model sweep was run. The result therefore says only how this pinned default Laya configuration behaved on this pinned engineering holdout.
