# Historical sample live rerun

The classification labels behind these numbers are a three-model consensus, not human gold.

The operator authorized this repeated-sample check in [issue #1](https://github.com/HiQS-Labs/Jev-unofficial-toolkit/issues/1#issuecomment-5752039443), explicitly overriding the normal one-live-run rule. It is not a fresh holdout or evidence of improved generalization. Original handoff receipts and questions are unchanged.

| Measurement | Historical receipt | This rerun |
| --- | --- | --- |
| Purpose correct | 88/100 | 89/100 |
| Purpose macro-F1 | 0.6868054177836787 | 0.7002285599360067 |
| Area correct | 60/94 | 62/94 |
| Purpose confidence >= 0.8: correct | 73/75 | 72/74 |
| Purpose confidence >= 0.8: coverage | 75/100 | 74/100 |

The original gate (accuracy >= 0.9 and coverage >= 0.6 at confidence >= 0.8) passes. Exact rerun metrics, confusion matrices and confidence buckets are in [results.json](results.json); historical comparison values are in the [frozen fixture](../../examples/fixtures/fresh-100/expected.json).

The source quiz from Needle-fork f7c7047 was checked against its original SHA-256 before conversion to the CLI schema. State used the identical Project / Title / Description template. Source text remained outside this repository; runtime visibility checks allowed only public HiQS-Labs repositories. [manifest.json](manifest.json) freezes transformed input, questions, labels and the unchanged gate. [verification.json](verification.json) records original request-hash comparison and offline MockClient rescoring of the retained live choices/confidences.

This was not an uninterrupted successful CLI evaluation. The first attempt failed before persisting results; its request count and usage are unknown. A checkpointed attempt retained the first 13 answers, then rejected the area probability distribution on record 14. A diagnostic request repeated that record; its valid choice/confidence was retained. The remaining records used JevClient and the existing scorer, retaining choices/confidences without invoking the optional probability accessor. This response-validation recovery was unrelated to correctness against labels; labels were opened for scoring after every retained answer was finalized. The sample and labels were already historically known, so this does not establish a newly blind experiment.

[Issue #6](https://github.com/HiQS-Labs/Jev-unofficial-toolkit/issues/6) tracks probability validation and failure persistence. The failing map was not retained; rounding is a hypothesis, not an established cause. No probability distribution was fabricated or normalized. The retained responses account for 133560 input tokens; total billed usage across failed attempts is unknown. No cost estimate is claimed.

[answers.json](answers.json) contains typed projections and original request/response hashes, not original API bytes or source state. [provenance.json](provenance.json) records the execution revision and recovery history. All 18 offline tests pass, and MockClient rescoring exactly matches the saved metrics and gate. CI remains mock-only. The older holdout and ATE fixtures were not rerun live; their existing offline reproduction limits remain unchanged.
