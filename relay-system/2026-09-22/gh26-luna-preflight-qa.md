# GH-26 Luna pre-inference QA — 2026-09-22

VERDICT: APPROVE
swept file: yes

Scope: complete receipt helper and focused tests, private collector, accepted Phase 0 trace shapes, and final focused-test/remapped-smoke logs. No train/holdout answers were opened; no scored calls or descendants were launched. Approval covers the reviewed implementation before inference, not a completed experimental result.

Reviewed SHA-256 commitments:

- Helper: `05b283403d825d14106141e735dd2359ed79758d50cce6259a72d6259e67a05b`
- Focused tests: `404f2c12ef0ea117ac58af4f6555f67c5d52543cf51ed1fc81e3562ed0898bdd`
- Private collector: `d5e733b4de834ee71dce143c08723995eee6c83c919579a3ece634d977db0283`

Resolved review findings:

1. The initial attestor copied the blind prompt hash without validating a plaintext launch request. It now validates the closed launch-request sidecar against the exact serialized blind row, checks requested task/model/effort/fork against the parent launch, and correlates parent ciphertext to child inbound ciphertext.
2. The initial attestor checked final-event text but not the assistant response item. It now requires exact agreement among the response item, final event, and completion record.
3. The runtime provider was not checked. The attestor now requires the observed `openai` provider alongside exact child model/effort settings.
4. Filtering inbound blocks could admit extra plaintext. The attestor now requires the exact real two-block shape: fixed NEW_TASK wrapper tied to the row task, then the matching encrypted-content block. Extra plaintext, wrapper changes, and extra block keys have rejection controls.

Evidence and boundaries:

- `attest_trace` binds the child to its parent/task, exactly one launch/session/turn/completion/final result, exact model/effort/fork, and full finalized trace bytes. Unknown response-item kinds and tool calls fail. Distinct session and trace hashes are checked across receipts by `validate_raw`.
- `parse_choice` rejects duplicate keys, prose, extra fields and invalid labels. Closed raw/freeze/provenance constructors constrain metadata and prevent text sentinels from crossing into published JSON.
- `finalize_receipts` commits the complete raw stream before scoring. `summarize` validates commitments before opening labels. `verify` independently rebuilds metrics, enforces frozen support/schema, and matches projected responses and provenance to separate commitments.
- The collector uses create-only row receipts and a persistent stop record on collection failure. The coordinator must still create each plaintext launch sidecar before its one authorized spawn, preserve ordering, and stop immediately on any scored failure.
- Reviewed focused logs show the initial parser red controls failed before correction and the final suite passed all 14 tests. Reviewed offline remapped checks accept both existing real smoke traces. These are validation of parsing/runtime shape, not additional scored inference.

Accepted limitation: local logs contain encrypted task payloads. The sidecar commits the coordinator's requested plaintext and ciphertext correlation binds parent to child; neither proves cryptographic equality of plaintext to delivered ciphertext. Subscription authentication remains the accepted session-level Phase 0 evidence, not a child-log claim. The implementation/provenance preserves this distinction.

No unresolved blocking implementation findings remain. Freeze these helper/test bytes and the blind-input commitment before inference. Final receipt QA and the full mock-only repository gate remain required before publication.

