# GPT-6 Luna: six-action next-action comparison

Contents: Limitations · Protocol · Original pass · Artifacts · Completed CLI rerun

## Limitations

This is a single engineering comparison on the same known 100 rows used in issue
#21. There are two held-out trajectories and no `git` truth rows. It does not
estimate general model superiority or authorize routing or deployment.

The task, serialized state, prescriptive instruction and six ordered action
definitions are shared with the historical arms. Codex adds its own system,
developer, environment and repository scaffolding and uses generated choice-only
JSON; these are not byte-identical requests or equivalent harnesses.

Model identity is attested by the executing Codex runtime's session record,
not a separate provider assertion. In the original subagent pass, encrypted task
payloads could not be independently decoded to prove plaintext equality. The
completed CLI rerun instead verifies its recorded plaintext task against the
exact dispatched bytes. Fresh sessions have no prior conversation, but share the
runtime environment and filesystem. No calibrated confidence is available.
Reported token usage, when present, includes harness scaffolding; monetary cost
is unavailable. Concurrency changes throughput, not the validity rule.

## Protocol

See [the frozen project plan](../../PROJECT/2-WORKING/GH-26-GPT6-LUNA-SUBAGENTS.md)
and [issue #26](https://github.com/HiQS-Labs/Jev-unofficial-toolkit/issues/26).
One fresh `gpt-6-luna` child at medium reasoning effort and `fork_turns="none"`
returns exactly `{"choice":"<one exact label>"}` for each row. The coordinator owns
the row index. Each completed trace must bind the requested model, effort and
fresh identity, contain one completed task and no tool calls. The first invalid
row stops the canonical pass; no row may be retried or supplied by the parent.

All 100 raw receipts must be finalized and hash-committed before the coordinator
opens labels. Scoring reuses `jev.eval.metrics`; independent verification
recomputes the aggregates and validates the frozen provenance commitments.
Committed per-row results contain only numeric indices, labels, correctness and
hashes. Raw source text, prompts, session logs, identifiers and machine paths
remain outside Git.

## Original pass — stopped incomplete

**Incomplete — no accuracy score.** The canonical pass launched 38 fresh Luna
children sequentially. Rows 0–36 produced 37 validated receipts. At row 37 (the
38th launch), the coordinator accidentally omitted “next” from the frozen first
sentence when transcribing the direct launch request. The coordinator noticed
the drift and stopped; the remaining 62 rows were not launched. There were no
retries, replacement predictions, label access, or partial scoring.

This is a coordinator orchestration failure, not evidence of a Luna model
failure or classification accuracy. The malformed request still received a
choice-only response; it cannot count toward the frozen benchmark.

The automated validator checked the saved plaintext request against the frozen
serializer and correlated encrypted parent/child payloads. It could not verify
that the manually transcribed actual launch used that saved plaintext. The
coordinator's self-review, not the validator, found the omission. Any future pass
needs exact programmatic dispatch from the frozen request plus a verifiable
binding, and separate operator authorization under this experiment's no-retry
rule. The frozen helper is retained unchanged as an audit artifact.

## Artifacts

- [Freeze manifest](freeze.json): helper/protocol committed at `96f4767`, then
  blind-input/runtime freeze committed at `4b0c19b`, both before inference.
- [Incomplete-run receipt](incomplete-run.json): counts, failure classification,
  intended/actual requested-prompt hashes, failed child-trace hash and partial
  raw-receipt hash. No source text, predictions or gold labels are published.
- [Data preflight](data-preflight.json): frozen input/baseline checks and source
  suite result (598 passed, 7 skipped, 18 deselected).
- [Pre-inference QA](../../relay-system/2026-09-22/gh26-luna-preflight-qa.md):
  reviewed helper and 14 passing focused controls, including two offline checks
  against completed synthetic runtime traces.

Private inputs, launch sidecars, the actual drifted request, 37 accepted receipts,
stop marker and test logs remain in the repository's ignored temporary folder.
Raw runtime session logs remain in Codex's private session store. The earlier
Phase 0 audit was relocated into this repository's ignored temporary folder.

## Validation

The full mock-only suite passed all 60 tests under Python 3.13. The initial
Python 3.9 invocation had two errors in existing HTTP-error mock tests
(`HTTPError.close()` reached a missing `file` entry in standard-library
`tempfile`). Both logs are retained privately and hashed in
[validation.json](validation.json). No code changed between invocations. This
explicit environment follow-up deviates from the planned single full-suite
invocation; it did not retry any scored model row.

[Final independent QA](../../relay-system/2026-09-22/gh26-luna-final-qa.md)
approves publication of this incomplete-run receipt only.

## Completed CLI rerun

The operator authorized up to three new attempts with adaptations, with the
prompt defect fixed first. The original failed pass above remains unchanged.
The new runner sends the serializer's exact UTF-8 bytes to a fresh Codex CLI
session via stdin, checks all 100 hashes before inference, and verifies equality
against the actual plaintext task in the runtime trace. No manual prompt copying
is involved. Official [Codex non-interactive documentation](https://learn.chatgpt.com/docs/non-interactive-mode)
and the installed CLI help document the stdin execution path.

This is an explicit harness pivot: fresh `codex exec` sessions, not collaboration
subagents. Model, medium effort, six options, task instruction, dataset and blind
prompt hashes remain fixed. User configuration is ignored; API-key overrides are
removed; ChatGPT subscription authentication is checked. Read-only execution and
runtime zero-tool validation apply. The CLI and prior subagent scaffolds differ.

[Preflight](rerun-preflight.json) records the two final synthetic checks: exact
runtime input matches, one completed fresh session, correct model/effort, valid
choice-only answers and zero tool calls. Seventeen new focused controls pass,
including an omitted-word regression, row-99 corruption preventing all calls,
repeated-prompt preservation, and stop-on-first-failure behavior.

**The first newly authorized attempt completed 100/100 valid rows and scored
30/100 (30% accuracy), with six-class macro-F1 0.1962121212121212.** There were
no row retries, tools, reused sessions, missing rows, substitutions or partial
scores. Attempts 2 and 3 were not used. The historical failed subagent pass remains
unscored and is not part of this result.

| Same known 100-row sample | Correct |
|---|---:|
| Phase-backoff baseline | 42 |
| Markov-1 baseline | 37 |
| **GPT-6 Luna, fresh Codex CLI, medium** | **30** |
| Needle tuned scorer | 28 |
| Majority baseline | 26 |
| SemIf/Qwen3.5-4B | 24 |
| Repeat-last baseline | 22 |
| Jev recorded original | 21 |

Historical model values are from the [SemIf comparison receipt](../2026-09-22-semif-six-action/README.md).
The prompt serializers/readouts and runtime scaffolds differ between arms.
These are observed scores on a reused sample, not a statistically established
ranking or evidence of broad model intelligence. There is no completed
GPT-5.6 Terra or Sol 100-row arm here; the earlier synthetic formatting checks
cannot be compared as accuracy results.

| Label | Gold support | Predicted | Correct | Recall |
|---|---:|---:|---:|---:|
| edit | 19 | 14 | 5 | 26.3% |
| git | 0 | 0 | 0 | n/a |
| read | 29 | 59 | 19 | 65.5% |
| run_command | 26 | 0 | 0 | 0% |
| run_tests | 7 | 13 | 2 | 28.6% |
| search | 19 | 14 | 4 | 21.1% |

The main observed weakness is zero `run_command` predictions despite 26 gold
rows, alongside 59 `read` predictions. The aggregate score therefore does not
support replacing the stronger phase-backoff baseline.

Summed runtime-reported agent duration: **334.011 seconds**. Reported usage:
1,411,243 input tokens (1,163,520 cached), 913 output tokens, 1,412,156 total;
zero reasoning-output tokens were reported. Usage includes CLI scaffolding.
Monetary cost and calibrated confidence are unavailable.

**Commit order:** reviewed code `ce7b6fd`; per-attempt freeze `cc9620c` before
inference; complete raw commitment `11e84b1` before opening labels. Raw SHA-256:
`21612297c6eaf8e3509af0e111dad0a6bfbb9256f383d31c0c723653a6283f00`.

- [Attempt freeze](rerun-attempt-1/freeze.json)
- [Pre-label raw commitment](rerun-attempt-1/raw-commitment.json)
- [Results and sanitized per-row projection](rerun-attempt-1/results.json)
- [Provenance](rerun-attempt-1/provenance.json)
- [Independent metric verification](rerun-attempt-1/verification.json)
- [Pre-inference QA](../../relay-system/2026-09-22/gh26-luna-rerun-preflight-qa.md)

All 77 mock-only tests passed on the frozen code under Python 3.13. The raw CLI
inputs, launch records, stdout and finalized runtime traces remain private in the
repository's ignored temporary folder. No source text, machine paths, session
identifiers or raw reasoning are included in the public result projection.

[Final independent CLI audit](../../relay-system/2026-09-22/gh26-luna-rerun-final-qa.md)
approves the completed 100-row result and its publication.
