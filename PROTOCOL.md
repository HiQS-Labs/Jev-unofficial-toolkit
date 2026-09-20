# Experiment protocol

The classification labels behind these results are a three-model consensus, not human gold.

The following protocol and question-design rules are reproduced verbatim from
[issue #1](https://github.com/HiQS-Labs/Jev-unofficial-toolkit/issues/1).
The linked issue explains the historical references; the corresponding receipts
are pinned in the [handoff snapshot](https://github.com/HiQS-Labs/Jev-unofficial-toolkit/tree/9b37264/handoff).

## Protocol rules

1. **Pin the model, log the model.** Send `jev-1.13.0`, never the alias; record the response `model` on every row. Aliases move and thresholds tuned on one version are not portable.
2. **Freeze the questions by commit before the first request; hash them.** `questions_sha256` in every results file. A wording change after a request is a new experiment with a new results directory.
3. **Read labels only after the last response is in.** The scorer must not be able to see truth while requests are outstanding. In #69 this was enforced structurally (labels opened after the loop) and, for the human-facing part, with a hash commitment of the blind annotation before the second annotator ran.
4. **Hash every request and response; store hashes, verdicts and aggregates; never the text.** Results directories in this repo contain no titles, descriptions or stderr. A toolkit's results writer should refuse those fields by name.
5. **Gate what leaves the machine.** Per-repo `PUBLIC` check via `gh repo view` at run time, skipped rows reported. The operator's rule (public HiQS-Labs only; previous-org, BinoidCBD, LTVera never) is a config, not a comment.
6. **Pre-register the gate, including the confidence floor.** #69's ≥ 90% accuracy / ≥ 60% coverage at ≥ 0.8 was written into the issue before the sample was drawn. #712's "no systematic disagreement the operator would not accept" was rejected by plan QA as unfalsifiable and replaced with numbers — correctly.
7. **One live run per frozen sample.** The runner refuses to write into an existing results directory.

## Question-design rules

1. **Criteria carry the boundary sentences, not just the label name.** "A comparison plan is research_evaluation, not planning just because it says plan" is what separates two classes Jev otherwise confuses. Full taxonomy bullets, verbatim.
2. **Choice, not Score, when you will compare against string labels.** Score-to-legend rounding is lossy for agreement metrics (plan QA finding, #712).
3. **The option set is the full union of what the reference emits.** `env_missing` was missing from the first draft and would have forced a wrong answer on 3 benchmark rows.
4. **Conflicting evidence → low confidence, and the answer follows the most literal signal.** Exit code 0 beat `Segmentation fault` for status. Write the exact condition ("a crash signature in stderr is a fail even with exit 0"), or decompose into a Noul per signal and combine in code.
5. **Undefined labels get script-authored glosses, recorded as such.** `ci_cd`, `skills`, `ui` have no definition in taxonomy v3; the glosses live in the results provenance so a taxonomy revision can adopt or replace them.
6. **Structured state works.** ATE rows went as a JSON object (`command`, `exit_code`, `edit_applied`, `stderr_tail`); classification rows went as the same `Project / Title / Description` string the baselines used. Keep the state identical to whatever the baseline saw.

## Applying them here

`jev-1.13.0` is the only accepted model. Question files have sidecars and
independently pinned hashes in `guard.py`; commit them before a live experiment.
A live manifest freezes the input file, questions, model, blind labels, and gate.
The CLI reserves a new output directory before sending requests, finalizes the
answers before opening labels, and projects typed results without copying state.
Failures leave the reserved directory in place; do not treat a partial run as a
completed experiment.

The results writer rejects the named fields recursively, including inside lists.
A field denylist cannot detect secret text renamed to an arbitrary field: callers
must use the typed projections and keep source text outside the repository.
For live CLI use, both the configured owner policy and the runtime PUBLIC check
must pass; skipped IDs are reported. Standalone `JevClient` is a transport primitive;
callers embedding it are responsible for applying the same guards.

The ATE question wording is newly authored from the handoff requirements and
includes the explicit crash and `expects_edits` rules. Replaying historical answers
does not validate that wording. Its hash identifies this toolkit's new question
set; historical request hashes remain separately identified.

Testing is paused by operator instruction. The final handoff-based implementation
has not been validated; the manual CI workflow has not been dispatched.
