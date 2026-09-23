# GH-26 Luna CLI rerun final QA — 2026-09-22

VERDICT: APPROVE — completed CLI arm
swept file: yes

Independently audited all 100 completed attempt-1 receipts, saved stdin, launch manifests, CLI events and finalized runtime copies; the public result/provenance/verification artifacts; and the final comparison documentation. The raw train/holdout answer sources were not opened. Public per-row labels were inspected only after the coordinator committed the complete raw receipt stream.

## Runtime and commitment audit

- All 100 saved stdin byte strings equal the frozen serializer output and the sole plaintext task input recorded after the runtime turn context.
- All 100 rows have distinct session identities, full-trace hashes and destination-bound launch hashes. Every trace records fresh source `exec`, provider `openai`, model `gpt-6-luna`, medium effort, and the frozen CLI version.
- Every row has one completed turn, one valid choice-only final answer, zero tool calls, matching CLI/runtime answers, and matching retained receipt data. No parent/fork session metadata is present.
- All saved row receipts match the complete private raw stream; all published choices/prompt hashes/trace hashes match those receipts. The run has a complete marker and no stop marker.
- The original failed subagent pass remains separate and unscored. This first newly authorized attempt completed successfully; attempts 2 and 3 were unused.
- Reviewed commit sequence: implementation `ce7b6fd`, per-attempt freeze `cc9620c`, and complete raw commitment `11e84b1`. The latter commit contains the raw commitment, before scoring artifacts were added. The coordinator's label-blind procedure is retained as an attestation; this review does not claim to prove arbitrary filesystem access history.

## Independent calculations

Rebuilt the confusion matrix directly from the public per-row projection, without the scorer's aggregate function:

- Correct: **30/100**, accuracy **0.30**.
- Six-class macro-F1: **0.1962121212121212**, including the unsupported git class as zero.
- Per-label supports, predicted counts, correct counts and recalls agree with results and the frozen support.
- Sum of runtime-reported task durations: **334,011 ms**; this is not a wall-clock throughput measurement.
- Usage: **1,411,243 input**, including **1,163,520 cached input**; **913 output**; **1,412,156 total**. Reported reasoning-output and cache-write input counts are zero. Raw receipt totals, commitment and provenance agree.
- Independent verification file hashes bind the exact result and provenance bytes reviewed.

Checked SHA-256 commitments:

- Complete raw stream: `21612297c6eaf8e3509af0e111dad0a6bfbb9256f383d31c0c723653a6283f00`
- Raw commitment: `bb149ea4a58101e48e6492fab3cfc6f1f0dccd9601ec24c69a00716b8b7f6d2b`
- Results: `3bad9f8647903eb7291df94627d72f4ac60010427ea855e78cc8f01578dd373e`
- Provenance: `9cf454e19b50eabd40696be2b5545381909f073fb2a0e56202f2931a7af0270c`

## Publication and interpretation

The five attempt JSON artifacts contain only the closed numeric/boolean/null structures, allowed schema/label/identity strings and hashes. All 469 string values passed an independent enum-or-hash check; no arbitrary source text, prompt, machine path, account/session identifier or raw reasoning value is published. The public links point to the relevant freeze, raw commitment, results, provenance and verification artifacts.

Documentation accurately distinguishes the completed fresh-CLI arm from the failed collaboration-subagent arm. The opening limitation now scopes encrypted input uncertainty to the original pass; the completed CLI arm verifies recorded plaintext against dispatched bytes.

The reported 30 exceeds the listed historical model point estimates and the majority baseline on this reused sample, but remains below Markov-1 at 37 and phase-backoff at 42. Different harnesses, only two trajectories, zero git truth support, one successful pass, unavailable monetary cost and uncalibrated confidence are explicitly disclosed. No statistical superiority, broad intelligence, deployment or substitution claim is justified.

The approved dispatcher/scorer/tests are unchanged from `ce7b6fd`. The reviewed pre-inference full gate passed all 77 mock-only tests under Python 3.13; no code change warrants another invocation. Diff whitespace checks pass. Final publication/hosted-check confirmation remains the coordinator's handoff task.

No unresolved blocking findings remain. Approve publication of the completed CLI result together with the preserved failed-pass history.

