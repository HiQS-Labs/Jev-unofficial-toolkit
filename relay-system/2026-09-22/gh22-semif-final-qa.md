# RELAY · GH-22 SemIf six-action final QA
<!--
  Single source of truth for this two-agent relay. Read the ENTIRE file before acting.
  Scaffolded by relay-automation/new-relay.sh on 2026-09-22.
-->

NEXT: Reviewer
STATUS: Open
ROUND: 2 / 3

## ▶ TAKE YOUR TURN — read this first (works for ANY agent: Claude, Codex, agy)
1. **Read this whole file** (header, Setup, Ground rules, every block in the Log).
2. **Check it's your turn:** `NEXT` (top) names the role to act. Confirm you are bound to it and the
   last Log block isn't already yours. If not → STOP and reply "wrong window — nudge the <other> window."
3. **Do your role's work** on the artifact named in Setup:
   - **Reviewer:** review vs the Definition of Done → graded findings
     (`[Blocker]`/`[Should]`/`[Nit]`/`[Pass]`), each with a concrete fix → set a **VERDICT**
     (exactly PASS, FAIL, or PARKED) and a **Basis** (explanation). **Review the whole file, not just the diff** (GH-268):
     a beta test had this loop reach `Approved` in two rounds while an independent audit of the same
     branch found 20 issues (1 critical, 4 high) — every one of them in the pre-existing code the
     change sat on, which nobody had read. Pre-existing defects in a file you are touching are IN
     SCOPE; if you find none, say so explicitly rather than leaving it unstated.
     **Declare it: every review block must contain a literal `swept file: yes` or `swept file: no`
     line.** Without it a reviewer that skipped the sweep is indistinguishable in the transcript from
     one that did it and found nothing — which is how the original 20 issues stayed invisible.
     Any `[Pass]` or "verified"/"confirmed" finding MUST
     carry a quoted span or a `file:line` citation — an uncited one is mechanically downgraded to
     `[Unverified — no citation]` (GH-173 B3). Do **not** edit the artifact; only append findings here.
     **A finding that asks for a behaviour change is a generalization unless you can paste the concrete
     input — a row, a value, a `file:line` — that fails under the current code** (GH-681: the gh673
     final QA relay generalized one late-error observation into "or a later invalid identity", the
     Producer implemented it, the same seat `[Pass]`ed it next round, and one historical NULL-URL
     ledger row then blanked every issue). Every `[Blocker]` or `[Should]` requesting a behaviour
     change MUST carry three lines: `Observed input:` (the failing input you saw), `Affected scope:`
     (the input predicate the change would govern), `Falsifier:` (the fixture or data that would show
     the change unnecessary or wrong, and its expected result).
     A `[Blocker]` must cite an observed failure. This is a protocol rule, not a mechanical check —
     the Producer may disposition a request lacking these as `Declined — unproven generalization`.
   - **Producer:** log a disposition for every open finding (Implemented / Modified / Declined + why,
     including `Declined — unproven generalization` for a behaviour-change request that carries no
     `Observed input:` / `Affected scope:` / `Falsifier:`), make the change, then add new work.
4. **Append ONE block** at the very bottom, directly **above** the marker line. Never edit earlier turns.
   Reviewer headings may be `### Reviewer · Round N`, `### Round N · Reviewer · <agent>`, `### Reviewer (<agent>)` (optionally followed by `— rN`), or `### Reviewer — Round N` (optionally followed by `(<agent>)`); follow the heading with a non-empty review body.
5. **Update the header:** flip `NEXT`; set `STATUS` (`Approved` closes — Reviewer only; else `Open`);
   the Producer bumps `ROUND` when opening a new cycle. If the max `ROUND` ends without `Approved`,
   set `STATUS: Escalated`.
6. **Commit only the relay file** (`relay(gh22-semif-final-qa): <role> r<N>`); no push. **Stop** and report one line.
7. **Hand off explicitly — EVERY turn, not just the first** (GH-268). End your turn by naming who acts
   next and what they should do: *"handing off to <other role> — go to the <other> window and say
   'take your turn'"*, or *"relay closed (Approved), no further turn needed"*. The beta report singled
   this out: the Reviewer turn never told the user to return to the Producer window, so a relay that
   was merely waiting looked stalled. A turn that ends without this line is not finished.

## Setup
- Artifact under review: **.relay-artifacts/README.md** — the read-only path that
  `relay-drive.sh --artifact-file /Users/noelsaw/marathon-clones/jev-gh22-semif-six-action/evidence/2026-09-22-semif-six-action/README.md` seeds into the isolated worktree (read it there; do NOT edit it).
- Reviewer: codex   ·   Producer: claude-a
- Started: 2026-09-22
- Definition of Done: Approve only if commit `6cb00c1f2921284b730eb9b747295637ac67ee06`
  faithfully reports the frozen 100-row SemIf run, the runner and independent verifier fail closed
  on the registered drift/safety cases, committed evidence contains no source text or machine-local
  paths, provenance and metrics are internally reproducible, documentation states the comparison's
  limits without overclaiming, and the change is ready for its one final repository-wide gate and PR.

## Review packet

Review the committed branch at
`/Users/noelsaw/marathon-clones/jev-gh22-semif-six-action`, exact HEAD
`6cb00c1f2921284b730eb9b747295637ac67ee06`, against `origin/main`. The seeded artifact is the
human-readable receipt, but the implementation review must sweep every changed file, especially:

- `evidence/2026-09-22-semif-six-action/semif_next_action.py`
- `tests/test_semif_evidence.py`
- `evidence/2026-09-22-semif-six-action/results.json`
- `evidence/2026-09-22-semif-six-action/provenance.json`
- `evidence/2026-09-22-semif-six-action/verification.json`
- `evidence/2026-09-22-semif-six-action/README.md`
- `PROJECT/2-WORKING/GH-22-SEMIF-SIX-ACTION.md`, `README.md`, and `ROADMAP.md`

The frozen runner commit recorded in provenance precedes result publication by design. Observed
evidence: 100/100 rows, 24 correct, macro-F1 `0.16750572534154626`, holdout SHA-256
`f016551eda2f9912c2ab81887669281452777ac103737f6e9b092044064a8587`, and raw-output SHA-256
`df2754fc413d85df80de922d6807933e4505ac8f5d9e68e5cf56401d88713777`.

Run focused checks as useful, but do not edit implementation files. The repository-wide unittest
gate is intentionally reserved until after final approval. The producer already observed:

- receipt-focused unittest: 5/5 pass;
- independent verification: valid and byte-stable when rerun;
- SemIf checkout: 78 passed, 1 skipped; raw checksums pass; 69 published claims verify;
- canonical cached-model pass: 68.94 seconds wall, no swaps.

Questions:

1. Do the committed metrics, projections, confusion/per-label counts, hashes, and prose agree?
2. Is the raw schema/model identity closed and source precision enforced before any result write?
3. Is verification meaningfully independent, and do red controls cover frozen-data, baseline,
   missing/duplicate/option, schema, revision, quantization, tampering, and sentinel leakage?
4. Can any state/query/prompt/issue text, arbitrary raw field, local path, cache, or weight leak into
   the committed artifacts through the implemented path?
5. Are model/data/source revisions, probability semantics, runtime envelope, sample limits, and the
   same-task-but-not-byte-identical distinction accurate and sufficiently prominent?
6. Is the footprint proportionate and free of unrelated runtime/API behavior changes?

Flag concrete correctness, safety, evidence, or publication problems. Do not request a production
adapter, extra benchmark arms, calibration work, model changes, or a generalized framework.

## Ground rules
1. This file is the single source of truth. The agents never share memory — read the whole file.
2. Take a turn only if `NEXT` names your role — otherwise reply "not my turn" and stop.
3. One turn = one block appended at the very bottom, above the marker. Never edit earlier turns.
4. Stay tight — findings are bullets, not essays. Grade every finding.
5. **The Reviewer never edits the artifact.** It proposes graded findings; the Producer implements.
6. The relay ends on **Approved** (Reviewer only). End each turn by committing just this file; no push.

## Log

### Reviewer · Round 1

swept file: yes

- [Blocker] The closed top-level raw schema still permits arbitrary raw text to cross the committed-evidence boundary through model metadata. `_validate_model` accepts any nonempty `mlx_version`, `mlx_lm_version`, and `transformers_version`, accepts arbitrary slash-free `source_artifact_sha256` keys, then copies those values into both `results.json` and `provenance.json` (`evidence/2026-09-22-semif-six-action/semif_next_action.py:201-239,327-350`). That contradicts the plan's fixed-constructor/no-arbitrary-raw-dictionary contract (`PROJECT/2-WORKING/GH-22-SEMIF-SIX-ACTION.md:83`) and the acceptance requirement that no state/query/issue text can enter committed results (`PROJECT/2-WORKING/GH-22-SEMIF-SIX-ACTION.md:97`). Probe command: `export PYTHONDONTWRITEBYTECODE=1 TMPDIR="$PWD/.relay-scratch/tmp"; python3 -c 'import importlib.util; p="/Users/noelsaw/marathon-clones/jev-gh22-semif-six-action/evidence/2026-09-22-semif-six-action/semif_next_action.py"; s=importlib.util.spec_from_file_location("probe_semif",p); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); sentinel="GH22-PRIVATE-STATE-SENTINEL-7f53"; raw={"source":m.MODEL_SOURCE,"revision":m.MODEL_REVISION,"backend":"mlx","mlx_version":sentinel,"mlx_lm_version":"0.32.0","transformers_version":"5.17.0","mlx_lm_source":{"url":"https://example.invalid/repo.git","vcs_info":{"vcs":"git","commit_id":m.MLX_LM_COMMIT,"requested_revision":m.MLX_LM_COMMIT}},"allocator_cache_limit_bytes":0,"dtype":list(m.DTYPES),"quantization":None,"source_artifact_sha256":{sentinel:"0"*64},"serving_config":"mlx-direct-v1"}; out=m._validate_model(raw); print({"accepted":True,"sentinel_in_projected_identity":sentinel in repr(out),"mlx_version":out["mlx_version"],"artifact_names":list(out["source_artifact_sha256"])})'`; exit `0`; decisive output: `{'accepted': True, 'sentinel_in_projected_identity': True, 'mlx_version': 'GH22-PRIVATE-STATE-SENTINEL-7f53', 'artifact_names': ['GH22-PRIVATE-STATE-SENTINEL-7f53']}`. Fix: validate the three runtime versions against the canonical pinned values, construct the artifact map from an exact allowlist of expected filenames while accepting only their SHA-256 values, and add a red control that injects the sentinel separately into an allowed version value and an artifact-map key and proves failure before either result file exists.
  Observed input: the raw model object in the quoted probe, with `GH22-PRIVATE-STATE-SENTINEL-7f53` in `mlx_version` and as a `source_artifact_sha256` key, is accepted and returned verbatim by `_validate_model`.
  Affected scope: any otherwise schema-valid raw SemIf row whose allowed model-metadata strings or source-artifact names contain state, prompt, issue, local-machine, or other arbitrary text.
  Falsifier: after the fix, the same probe raises `ValueError`, the synthetic sentinel red controls leave both result paths absent, and the canonical metadata currently shown at `results.json:96-123` still validates unchanged.
- [Pass] The committed receipt itself is internally consistent: `results.json:11-168,2071-2089` reports 100/100, 24 correct, macro-F1 `0.16750572534154626`, the documented confusion/per-label/prediction counts, probability buckets, timing, and probability semantics; `verification.json:3-131` independently repeats the registered aggregates and binds results/provenance with their exact hashes; `README.md:3-35` reports the same values and comparison limits.
- [Pass] The main raw-result path otherwise fails closed before writes: exact input/raw/model field sets, sequential IDs, option order, finite normalized probabilities, timing, pinned source/revision/backend/dtype/quantization/readout, and run-wide identity are checked at `semif_next_action.py:189-278,297-314`; only after all rows validate do the create-only writes occur at `semif_next_action.py:352-353`. Registered red controls cover the frozen holdout/baselines, raw schema, revision, quantization, missing/duplicate IDs, option drift, and metric tampering at `tests/test_semif_evidence.py:125-180`.
- [Pass] Verification is meaningfully separate for the promised aggregate scope: independent implementations recompute confusion, accuracy, macro-F1, per-label counts, and probability buckets from committed typed projections at `semif_next_action.py:357-430`; the receipt accurately calls this aggregate reproduction at `README.md:7,37-44` rather than claiming byte-identical requests or broader model validation.
- [Pass] Provenance and prose are appropriately bounded: exact data/model/source revisions and hashes are recorded at `provenance.json:9-58`, the same-task-but-not-byte-identical and uncalibrated-probability limits are prominent at `README.md:24-31`, and the two-trajectory/repeated-sample/no-git-support limits are explicit at `README.md:46-48` and repository `README.md:135-137`. The footprint is additive and proportionate; no unrelated runtime/API behavior change was found. No additional pre-existing defects were found in the swept files.

VERDICT: FAIL

Basis: the frozen committed numbers, hashes, projections, verifier, and documentation agree, but the demonstrated nested-metadata pass-through violates the Definition of Done's no-arbitrary-raw-text leakage requirement. One narrow validator/test correction is required before approval.

Handing off to Producer — go to the Producer window and say "take your turn".

### Producer · Round 1 disposition

- Blocker, nested model-metadata text pass-through: **Implemented** in commit
  `4b8f6d5a5ef67039fd8f7a161ff5e107e33d08bf`. The three runtime versions are exact pinned
  constants; `source_artifact_sha256` must have the exact 11 canonical filenames and SHA-256-only
  values; and the MLX-LM URL and allocator limit are also pinned because the same differential probe
  showed they were previously accepted when mutated. The projection remains a fresh fixed
  constructor rather than a copied raw model object.
- Red controls: **Implemented.** Separate version-value and artifact-key sentinel cases now assert
  `ValueError` and prove both results and provenance paths remain absent. The focused suite remains
  5/5 green. The reviewer's original probe now raises; isolated version, artifact-key, URL, and
  allocator mutations all reject, while the actual canonical raw model metadata still validates.
- Receipt binding: **Updated** in commit `0fd1935`. The same raw output was re-summarized with the
  corrected runner; top-1, macro-F1, results bytes, and raw-output hash are unchanged. Provenance now
  pins toolkit commit `4b8f6d5a5ef67039fd8f7a161ff5e107e33d08bf` and runner SHA-256
  `21c25434e9c6b51d11d7271003889e87bfd5a0cc7f4d01f1e93a07a86537d145`; the independent verifier
  is valid and binds the refreshed provenance SHA-256
  `da265f8146137015bfb08929156f87d4ccae1a6f39e87b1cf37e310e58c5ad43`.

Please review current implementation HEAD `0fd1935` plus this relay-only disposition commit. The
repository-wide gate remains intentionally unrun until final approval.

Handing off to Reviewer — take round 2 and verify the blocker disposition against the corrected
validator, red controls, canonical metadata, and refreshed receipt.

<!-- ↓↓↓ NEXT TURN goes here (append above nothing — this marker stays last) ↓↓↓ -->
