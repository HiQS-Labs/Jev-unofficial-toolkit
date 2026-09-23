# GH-26 Luna plan QA — 2026-09-22

VERDICT: APPROVE
swept file: yes

Reviewed the complete GH-26 plan and the applicable SemIf loader, scoring, verification, and results-writer seams. No holdout answers were opened; no model calls or descendants were launched. This is plan approval, not implementation or experimental-result approval. Phase 0 runtime attestation is accepted as supplied by the coordinator; provider-level attestation remains unavailable.

The producer resolved the two plan gaps identified during review:

1. Freshness and runtime binding: the original Phase 4 raw-field list omitted a unique agent/session identity despite requiring reused-agent rejection. Execution decisions now retain `agent_id_sha256` independently of the full finalized trace hash; bind coordinator task identity to the parent launch record and child session; require one task, one turn context, matching completion and one final output; and reject unknown/tool-call response-item kinds.
2. Provenance verification: the existing SemIf verifier hashes supplied provenance without independently validating it. Execution decisions now require a closed provenance schema, frozen constants, and comparisons against the committed freeze manifest and finalized raw commitment. Local extraction derives metadata from the exact hashed runtime/launch artifacts instead of trusting supplied flags.

The amended plan also explicitly rejects duplicate JSON keys before child-output projection.

Approved properties, with plan references:

- Exact `gpt-6-luna` / `medium` / fresh `fork_turns=none` binding and candid runtime-evidence limitations: Execution decisions and Exact model and harness.
- Label blindness, separate preparation worker, frozen blind-input commitment and labels opened only after final receipt commitment: Execution decisions; Phases 2 and 4.
- One pass, no retries/substitution/resumption, and invalid rows stop the entire run: Frozen comparison contract; Phase 4 steps 2–6.
- Closed child/raw/committed boundaries, source-text sentinel controls and create-only persistence: Execution decisions; Phase 3; Phase 5 steps 1–2. The recursive writer is only a key-denylist backstop; the fixed typed projection remains the actual text boundary.
- Independent aggregate recomputation and provenance-tampering rejection: Execution decisions; Phase 5 step 5. Reuse `jev.eval.metrics` for summarization, not for the independent calculation.
- Commensurate additive scope and explicit repeated-sample, two-trajectory, zero-git-support, harness and confidence limitations: Expected write set; Phase 5 steps 3–6; Non-goals.

No unresolved blocking plan findings remain. Implementation QA must inspect the actual runtime extraction/launch binding and its negative controls, not only synthetic projected receipts. Freeze helper/tests and blind-input commitment before scored inference; retain final independent QA and the full mock-only gate before publication.

