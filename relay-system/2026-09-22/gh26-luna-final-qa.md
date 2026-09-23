# GH-26 Luna final QA — 2026-09-22

VERDICT: APPROVE — incomplete-run publication only
swept file: yes

The canonical benchmark is incomplete and must not be resumed or scored. Approval covers publishing the frozen implementation and candid failure receipt; it does not approve an accuracy result or claim the 100-row objective was achieved. The full mock-only gate passed under Python 3.13 after the explicitly recorded Python 3.9 failure below.

Independent audit:

- Recomputed all 37 retained receipts from their finalized child traces, parent launch records, blind rows and intended launch sidecars. Every recomputed receipt exactly matched its saved projection, and the combined uniqueness/order checks passed.
- The parent runtime contains exactly 38 sequential canonical launches, row_000 through row_037, without repeated canonical launch names. There are 38 corresponding child traces. Row 37 completed with a valid choice-only, zero-tool trace, but has no accepted row receipt.
- Compared the privately retained actual row-37 request to the frozen serializer. The sole difference is omission of “next” from “single best next broad action”. Actual and intended prompt hashes match the stop marker and public incomplete-run receipt.
- Rechecked the frozen helper identity and blind-file commitment without opening train or holdout answers. Checked the partial raw stream's hash against the public receipt.
- Confirmed that attestation using the intended sidecar accepts the row-37 runtime trace despite the actual launch drift. The runtime ciphertext does not prove that manually transcribed plaintext matched the sidecar. This was coordinator-detected drift, not an automated-validator success.
- Inspected the incomplete-run receipt and final documentation: no accuracy, macro-F1, partial score, predictions or gold labels are published. The 38 launched / 37 receipt-validated / 62 not-launched counts agree. The documents explicitly prohibit resuming this pass and require separate authorization for a future pass.
- The frozen helper and focused tests remain unchanged. No new inference, retry, model substitution, descendant or label access occurred during this review. The coordinator's no-label-access statement is retained as a procedural attestation; it is not an independently proven property of arbitrary filesystem activity.

Checked commitments:

- Freeze manifest: `a64060b4fbc55c39ef92b3fc97c4742377aff8277db47823adf38e663198fc07`
- Failed child trace: `0355c7be80b1e7f448ec92809b3869b554274bd54bd933b14c950e888494c1db`
- Partial raw receipts: `6d45410985e6aa4e6868fe15a0bdd0313169b49ef5e7ad5f7328922545546dcb`
- Intended row-37 prompt: `be196de082fe60df60b9fe3ef4328b17eacbfef40a57c25d1bccab09912eab4f`
- Actual row-37 requested prompt: `28a6c8de6acaeb476d8793b533173d38d3c8c7719fa85ac145163940aaaf48b9`

“Validated receipts” means the runtime and intended-sidecar checks passed; it does not establish independently verified plaintext delivery for the first 37 rows. The entire run is invalid for the frozen comparison regardless, so no inference about model performance follows.

No unresolved blocking findings remain for this failure disposition. Preserve the private raw evidence and publish the incomplete status visibly. A future implementation needs mechanically exact dispatch and an honest account of what its request binding proves; this audit does not authorize a new scored pass.

## Full-gate follow-up

Reviewed both retained logs. The initial default Python 3.9 invocation ran 60 tests and ended with two errors in existing HTTPError.close mock cases: test_mock_transport_retry_and_raw_response_hash and test_openrouter_canned_http_retries_and_exact_wire_hash. Both traces end in the Python 3.9 tempfile implementation with KeyError: file. The coordinator then ran the unchanged code once under installed Python 3.13; all 60 tests passed. This is a disclosed deviation from the planned single full-suite invocation, justified by the failed gate and environment follow-up. It is not a scored-model retry. No frozen implementation change accompanied the follow-up. The root README's incomplete-run note is now placed beside the existing model comparisons.
