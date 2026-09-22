# SemIf six-action comparison

SemIf scored **24/100** (accuracy `0.24`, macro-F1 `0.16750572534154626`) on the exact frozen 100-row holdout used for the Jev next-action result in [issue #21](https://github.com/HiQS-Labs/Jev-unofficial-toolkit/issues/21). It exceeded repeat-last (`22`) and Jev's recorded original result (`21`) and replay range (`18–21`), but did not exceed majority (`26`), Needle's tuned scorer (`28`), Markov-1 (`37`), or phase-backoff (`42`). This is a repeated-sample engineering comparison, not evidence of statistical superiority or broader generalization.

## Decision

The result does not justify a SemIf integration or replacement claim. It is a valid, reproducible adjacent measurement: all 100 rows scored, no rows were skipped, source precision was preserved, and an independent verifier reproduced the aggregates from the committed typed projections.

| Arm | Correct / 100 |
|---|---:|
| Phase-backoff | 42 |
| Markov-1 | 37 |
| Needle tuned scorer | 28 |
| Majority | 26 |
| **SemIf, Qwen3.5-4B direct MLX** | **24** |
| Repeat-last | 22 |
| Jev original | 21 |
| Jev replay range | 18–21 |

SemIf predicted `edit` 44 times, `read` 38, `search` 17, and `run_tests` once; it never predicted `run_command` or `git`. Recall was `9/19` for `edit`, `12/29` for `read`, `0/26` for `run_command`, `1/7` for `run_tests`, and `2/19` for `search`. The holdout has no `git` examples, so git behavior is not measured.

## Frozen comparison

- Dataset: `nebius/SWE-rebench-openhands-trajectories`, revision `35455389ab51bf5e2306bfd436ef72d0f98bf882`, CC BY 4.0.
- Holdout: 100 q1 rows from two OpenHands trajectories; SHA-256 `f016551eda2f9912c2ab81887669281452777ac103737f6e9b092044064a8587`.
- Task: predict one of `edit`, `git`, `read`, `run_command`, `run_tests`, or `search` from the same rows, q1 state, prescriptive criterion, and option descriptions as #21.
- SemIf: commit `1f2dea3e25379f9dfc98cb83c324f00ab5deda37`; `direct` mode; MLX backend; source precision; no quantization.
- Model: `Qwen/Qwen3.5-4B` revision `851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`; MLX-LM commit `a63e24c389382619eb6d9af656e3b46024be217a`.
- Input/output hashes: `11bd8f2714ab73feb07e44b6da65785d8bd9a7999d1cb95581d7f0aeec610024` / `df2754fc413d85df80de922d6807933e4505ac8f5d9e68e5cf56401d88713777`.

The task/state/options are the same, but the requests are not byte-identical: SemIf uses its own prompt serializer and a native last-position option-logit readout. Its reported probabilities are conditional scores over the declared options, not calibrated decision confidence. Eighty rows had a maximum option probability below `0.5`; 20 were in `0.5–0.8`; none reached `0.8`.

## Run envelope and verification

The canonical cached-model pass took `68.94s` wall time. SemIf reported `59.05398636700738s` summed per-row total time (`0.5734887085000082s` median). The process recorded a `9,686,961,152`-byte peak memory footprint and no swaps on Darwin arm64 with Python `3.11.15`, MLX `0.32.2`, MLX-LM `0.32.0`, and Transformers `5.17.0`.

SemIf's own checkout passed `78` tests with `1` skipped, all published raw checksums, and `69` published-summary checks before the run. The receipt-local focused suite covers the frozen holdout/baselines, closed raw schema, model revision and source precision, duplicate/missing/option drift, text-safety sentinel, and independent verification.

- [`results.json`](results.json) contains only allowlisted predictions, hashes, timings, model identity, and aggregate metrics.
- [`provenance.json`](provenance.json) pins data, source, runner, input, output, and model artifacts.
- [`verification.json`](verification.json) independently reproduces the metrics and binds the other two files by SHA-256.
- [`semif_next_action.py`](semif_next_action.py) prepares, summarizes, and verifies the frozen arm; [`test_semif_evidence.py`](../../tests/test_semif_evidence.py) provides the red and green controls.

Raw third-party trajectory text, serialized prompts, model weights, caches, and raw SemIf output are intentionally not committed. The retained per-row projection contains only indices, labels, probabilities, hashes, token counts, and timings.

## Limitations

The sample is already known, contains only two trajectories, and has no git support. Its labels are the existing #21 labels, not a new independent human reference. No wording, richer-state, calibration, quantization, or alternate-model arm was run. The result therefore says only how this pinned SemIf configuration behaved on this pinned engineering holdout.
