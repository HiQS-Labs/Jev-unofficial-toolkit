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

Choice-only synthetic Phase 0 and independent plan review passed. Canonical
inference has not started. This document will be updated with the actual terminal
state and verified result; it does not currently claim benchmark accuracy.

## Artifacts

The helper and focused tests are frozen before inference. The blind input's hash
is committed while its text stays outside Git. Completed results, provenance and
independent verification will be added only after a valid finalized pass.
