# GPT-6 Luna: six-action next-action comparison

Contents: Limitations · Protocol · Status · Artifacts

## Limitations

This is a single engineering comparison on the same known 100 rows used in issue
#21. There are two held-out trajectories and no `git` truth rows. It does not
estimate general model superiority or authorize routing or deployment.

The task, serialized state, prescriptive instruction and six ordered action
definitions are shared with the historical arms. Codex adds its own system,
developer, environment and repository scaffolding and uses generated choice-only
JSON; these are not byte-identical requests or equivalent harnesses.

Model identity is attested by the executing Codex runtime's child session record,
not a separate provider assertion. Requested prompt hashes bind the coordinator's
frozen messages; the encrypted payload in the local runtime trace cannot be
independently decoded. Fresh children have no prior conversation, but share the
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

## Status

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

## Newly authorized rerun

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

Each attempt will receive its own frozen manifest before inference. The first
fully valid 100-row pass is committed before labels and scored once. Failed
attempts are retained unscored; there are no row retries or best-of-three score
selection. No new scored attempt has started at this preflight checkpoint.
