# Use cases and evidence

**The classification labels behind these numbers are a three-model consensus, not human gold.** Agreement with those labels can reflect shared model errors. The ATE benchmark is synthetic with labels known by construction; its separate error-log reference is Gemma, not that classification consensus.

These are historical findings from the read-only [handoff snapshot](https://github.com/HiQS-Labs/Jev-unofficial-toolkit/tree/9b37264/handoff), interpreted under [issue #1](https://github.com/HiQS-Labs/Jev-unofficial-toolkit/issues/1). The final toolkit revision has not been tested at the operator's request. Its fixtures and test assertions target these receipts; this page does not claim new live measurements or completed acceptance.

| Use case | Recorded evidence | Verdict and boundary |
| --- | --- | --- |
| Closed-set work-purpose classification | Older holdout: `37/40`, macro-F1 `0.6753787878787879`. Fresh sample: `88/100`, macro-F1 `0.6868054177836787`; confidence ≥ `0.8` selects `75/100`, with `73/75` correct. [Holdout receipt](https://github.com/HiQS-Labs/Jev-unofficial-toolkit/blob/9b37264/handoff/needle-fork/TESTS-RESULTS/2026-09-18-jev-purpose-zero-shot/results.json), [fresh receipt](https://github.com/HiQS-Labs/Jev-unofficial-toolkit/blob/9b37264/handoff/needle-fork/TESTS-RESULTS/2026-09-19-jev-fresh-sample/jev/results.json). | **Proven on these recorded samples.** The fresh pre-registered gate was met. This is not a claim about other taxonomies, private data, or future samples. |
| Component-area classification | Older holdout: `32/38`. Fresh sample: `60/94`; in its confidence buckets, `5/22` correct below `0.5`, and `45/53` at or above `0.8`. [Holdout receipt](https://github.com/HiQS-Labs/Jev-unofficial-toolkit/blob/9b37264/handoff/needle-fork/TESTS-RESULTS/2026-09-18-jev-purpose-zero-shot/results.json), [fresh receipt](https://github.com/HiQS-Labs/Jev-unofficial-toolkit/blob/9b37264/handoff/needle-fork/TESTS-RESULTS/2026-09-19-jev-fresh-sample/jev/results.json). | **Not ready unattended.** Taxonomy ambiguity and model errors both matter. Area confidence is a weaker routing signal. |
| Failed-run triage: status, severity, category | Benchmark: FN `1`, FP `0`, with `24` known failures. Error-log agreement: status `143/143`, category `6/143`, severity `70/143`. [Benchmark receipt](https://github.com/HiQS-Labs/Jev-unofficial-toolkit/blob/9b37264/handoff/xyz-forge/TESTS-RESULTS/2026-09-18+GH-712/benchmark/summary.json), [error-log receipt](https://github.com/HiQS-Labs/Jev-unofficial-toolkit/blob/9b37264/handoff/xyz-forge/TESTS-RESULTS/2026-09-18+GH-712/errorlog/summary.json). | **Promising, but the gate was missed as written.** The error-log category reference was itself unfit; disagreement is not automatically a Jev error. No deployment flag followed. |
| Free-text causes or rationale | Not attempted; Jev provides typed decisions rather than generated prose. [Issue #1](https://github.com/HiQS-Labs/Jev-unofficial-toolkit/issues/1), [TypeSafe introduction](https://docs.typesafe.ai/introduction). | **Out of scope by design.** A generative model is needed when prose is the deliverable. |

## Confidence-gated routing

The fresh purpose gate was registered at accuracy ≥ `0.9` and coverage ≥ `0.6`, evaluated at confidence ≥ `0.8`. The observed `73/75` correct and `75/100` coverage cleared it. These fractions are kept exact rather than reporting a rounded percentage. See the [recorded gate](https://github.com/HiQS-Labs/Jev-unofficial-toolkit/blob/9b37264/handoff/needle-fork/TESTS-RESULTS/2026-09-19-jev-fresh-sample/jev/results.json).

The supported application pattern is to act on sufficiently confident purpose answers and route other rows to review or `uncertain`. That pattern needs a new baseline and gate before transfer to another deployment. The [fresh experiment summary](https://github.com/HiQS-Labs/Jev-unofficial-toolkit/blob/9b37264/handoff/needle-fork/TESTS-RESULTS/2026-09-19-jev-fresh-sample/SUMMARY.md) also records the label-adjudication limitations; consensus is not independent human verification.

## Why triage did not clear its gate

The missed benchmark row paired a successful exit with a crash signature. Its retained status is `pass` at confidence `0.05`, while its category is `crash` at confidence `0.75`. This illustrates the literal-reading failure described in the protocol: contradictory signals can produce low-confidence status without changing the argmax. See [benchmark rows](https://github.com/HiQS-Labs/Jev-unofficial-toolkit/blob/9b37264/handoff/xyz-forge/TESTS-RESULTS/2026-09-18+GH-712/benchmark/rows.jsonl) and the [historical interpretation](https://github.com/HiQS-Labs/Jev-unofficial-toolkit/blob/9b37264/handoff/xyz-forge/TESTS-RESULTS/2026-09-18+GH-712/SUMMARY.md).

The same summary records a zero-FN probability threshold of `0.48`. It was not the pre-registered argmax gate, so it does not turn the failed experiment into a pass. The raw probability map was not retained; confidence is not an exact replacement for it. The toolkit can recompute FN/FP from recorded choices and quote that threshold, but cannot independently recover its exact value from these rows. A new gate is a new experiment.

The error log repeats a homogeneous failure cause. The receipt attributes the poor category agreement to Gemma treating a missing required environment setting as authentication failure; status agreement in that corpus measures consistency, not discrimination. Its [plan](https://github.com/HiQS-Labs/Jev-unofficial-toolkit/blob/9b37264/handoff/xyz-forge/PROJECT/GH-712-JEV-ATE-TRIAGE.md) records the decision not to start the deployment phase. This toolkit adds no serving or hook integration.

## Untested hypotheses

All of the following are hypotheses from [issue #1](https://github.com/HiQS-Labs/Jev-unofficial-toolkit/issues/1), not demonstrated capabilities:

- Noul checks for whether an issue remains valid or is already fixed.
- Noul checks for whether proposed clusters share a root cause.
- Guardrail screening of agent transcripts before corpus ingestion.
- A second decision stage for anomaly rows, once the necessary error text is retained.
- Batching records into shared state to reduce repeated criteria, provided independence is demonstrated.

Each needs its own baseline, data policy, frozen question set, and pre-registered gate. None inherits the classification experiment's outcome. The possible SemIf/laya integrations listed in [README.md](README.md) are also untested; no adapters or compatibility claims ship here.
