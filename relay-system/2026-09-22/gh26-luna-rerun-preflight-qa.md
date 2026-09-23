# GH-26 Luna CLI rerun preflight QA — 2026-09-22

VERDICT: APPROVE
SWE verdict: Ship — bounded, separately identified CLI attempts with exact runtime input verification.
swept file: yes

Reviewed the authorized rerun amendment, complete new dispatcher/scorer and both focused test modules, retained dispatch red/green logs, and completed synthetic CLI smoke traces. No train/holdout answers were opened and no model processes were launched by this reviewer.

Approved code SHA-256:

- Dispatcher: `1e3c89fb568324610defc0e4b68fd10c165283539dc38337eb2d75fdafbc9294`
- Scorer: `5d8e9f23fcfd9c47af644ba5a4f484fc600300f224420e2d2d70b43dbfd1e136`
- Dispatch tests: `89df6bd4073e03b0163f6049810a6cc3337813a789a492cae805a3fced7280ea`
- Scoring tests: `f8de6ae0b23cac306f5eb0c9c7e837ef9be280919e12237e3f36fc4d57789e56`

Resolved findings:

- Runtime assistant validation originally filtered only final messages, admitting additional commentary. It now requires exactly one assistant message, its final phase, and exact agreement with CLI output and runtime completion.
- Frozen rows contain repeated prompts at indices 0/16 and 61/83. Requiring unique launch hashes would have rejected these valid rows when launch manifests contained only prompt/configuration. Manifests now bind their distinct private destination, while prompts remain unchanged and sessions/traces remain unique. A positive duplicate-prompt test preserves both rows.
- New CLI provenance now explicitly records subscription auth and Codex version. Preflight checks actual login status in the filtered environment and the installed version before model execution.
- Added loop controls cover corruption in row 99 before any subprocess, first-row attestation failure without a later launch, and second-row process failure with retention of the first receipt and no continuation.

The decisive omitted-word red control is retained. Reviewed final focused output reports 17 passing tests (7 dispatcher/attestation/loop tests and 10 scoring tests). Tests use synthetic inputs and mocked processes.

Reviewed the final Python 3.13 full-suite log: all 77 mock-only tests passed on this reviewed code. The public rerun-preflight artifact and README agree with the final smoke hashes, test counts, three-attempt cap and zero scored starts at this checkpoint.

Smoke evidence:

- Final smoke C runtime SHA-256: `27024a886fff840e80dcc16579978a8a7872e127cf4b6fa37728df2eafa2f382`
- Final smoke D runtime SHA-256: `f653a9b481a3027b0d00bc6c086d85c176e9db169d3c5ff1fbad531bcad4d69c`

Independently inspected both final smoke copies: each records source `exec`, provider `openai`, model `gpt-6-luna`, effort `medium`, and a sole runtime task message exactly equal to saved stdin bytes. Destination-bound launch manifests and finalized trace hashes match their retained receipts. The reviewed attestor rejects tool activity, reused/multiple turns, mismatched input/output and incomplete traces. These are synthetic smoke checks, not scored rows.

Protocol and implementation boundaries:

- All 100 blind rows and hashes are checked before the first model process. The checked UTF-8 bytes themselves go to stdin through an argv-list subprocess; no shell interpolation, manual transcription or appended prompt is used.
- Fresh CLI sessions are explicitly a different harness from collaboration subagents. Original failed-pass evidence and original frozen helper/tests remain intact. New schemas use `fresh_exec`, without misrepresenting it as subagent fork isolation.
- Each attempt is create-only; a failed launch or attestation stops its loop and retains evidence. The authorization permits at most three new attempts, adaptation only between attempts, no row retry/resume/prefix joining, and stopping after the first fully valid pass. The coordinator owns enforcement of the campaign-wide three-attempt cap and first-success stop.
- Separate closed CLI freeze/raw/result/provenance schemas reuse existing constants, parsing, loaders, metric implementation and create-only writer. Independent verification rebuilds metrics and binds response/provenance commitments. Labels remain unopened until a successful complete 100-row raw commitment.
- Private prompts, runtime traces, paths and launch metadata stay outside Git. Published projection remains labels/counts/hashes. Provider-level model assertion and cross-harness equivalence are not claimed.

No unresolved blocking findings remain. Commit the reviewed implementation and per-attempt freeze before scored inference, preserve every attempt's terminal status, and complete final result QA before publication. The full mock-only gate is satisfied for these unchanged code bytes. This approval does not itself claim a successful benchmark result.
