# RELAY · GH-25 Laya six-action final implementation QA
<!--
  Single source of truth for this two-agent relay. Read the ENTIRE file before acting.
  Scaffolded by relay-automation/new-relay.sh on 2026-09-22.
-->

NEXT: Reviewer
STATUS: Open
ROUND: 3 / 3

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
6. **Commit only the relay file** (`relay(gh25-laya-final-qa): <role> r<N>`); no push. **Stop** and report one line.
7. **Hand off explicitly — EVERY turn, not just the first** (GH-268). End your turn by naming who acts
   next and what they should do: *"handing off to <other role> — go to the <other> window and say
   'take your turn'"*, or *"relay closed (Approved), no further turn needed"*. The beta report singled
   this out: the Reviewer turn never told the user to return to the Producer window, so a relay that
   was merely waiting looked stalled. A turn that ends without this line is not finished.

## Setup
- Artifact under review: `evidence/2026-09-22-laya-six-action/` plus the complete origin/main-through-`b00cde7` implementation diff. Read that directory, `tests/test_laya_evidence.py`, `PROJECT/2-WORKING/GH-25-LAYA-SIX-ACTION.md`, `README.md`, and `ROADMAP.md` in full, including committed prediction rows and JSON contracts where material. Ignore this temporary relay transcript itself.
- Reviewer: codex   ·   Producer: claude-a
- Started: 2026-09-22
- Goal: determine whether GH-25 truthfully and reproducibly publishes the one canonical Laya run authorized by the approved plan.
- Operational envelope: one local CPU evidence receipt. No Jev runtime integration, Laya source modification, dataset redesign, alternate model arm, or production promotion. Complexity and tests must remain commensurate with a one-shot research receipt.
- Definition of Done: the implementation enforces the frozen input/model/question identities before inference; records the default English Router/CPU/float32 arm; preserves the instruction/options; measures state truncation; produces closed text-free schemas; independently reprojects raw evidence; reports the measured 15/100 result and limitations accurately; and introduces no unrelated runtime behavior.

### Review questions

1. Does `laya_next_action.py` fail closed on holdout/baseline/question/model/runtime drift, route drift, head truncation, schema drift, rounded probability errors, token inconsistencies, duplicate/missing rows, or create-only output reuse?
2. Does `run` exercise Laya's recommended Router-selected root English checkpoint at the pinned snapshot on CPU/float32, and are token counts and native rounded choice/tie behavior handled correctly?
3. Does `verify` consume enough frozen/raw evidence to independently reconstruct every committed row, aggregate, model identity, and binding hash rather than trusting committed JSON?
4. Can trajectory/source text, a local path, cache path, or unrestricted nested metadata reach committed JSON? Are schemas and relations closed as planned?
5. Do focused tests falsify credible failure paths, including raw route/head/choice/probability mutations? Is any missing test significant within this one-shot envelope?
6. Do all JSON and Markdown artifacts agree exactly on result, revisions, hashes, truncation, confidence limitations, native-test evidence, and lifecycle state?
7. Is any machinery unnecessary, duplicated beyond independent verification needs, or unsafe? Flag only concrete defects within scope.

Return graded findings with exact `file:line` citations. Every requested behavior change must include Observed input / Affected scope / Falsifier. Approve only if the branch is ready for the one final full repository gate and PR publication.

## Ground rules
1. This file is the single source of truth. The agents never share memory — read the whole file.
2. Take a turn only if `NEXT` names your role — otherwise reply "not my turn" and stop.
3. One turn = one block appended at the very bottom, above the marker. Never edit earlier turns.
4. Stay tight — findings are bullets, not essays. Grade every finding.
5. **The Reviewer never edits the artifact.** It proposes graded findings; the Producer implements.
6. The relay ends on **Approved** (Reviewer only). End each turn by committing just this file; no push.

## Log

### Reviewer · Round 1 (codex)

swept file: yes

- [Should] The frozen Laya source commit is asserted, not enforced. `LAYA_COMMIT` is a constant at
  `evidence/2026-09-22-laya-six-action/laya_next_action.py:57`, while `_model_identity` checks model
  artifact hashes and distribution versions but unconditionally emits that commit
  (`laya_next_action.py:281-295`); `run` imports and executes the installed package without inspecting
  any Laya source path or digest (`laya_next_action.py:332-353`). A same-version modified
  `laya==0.3.6` therefore passes the pre-inference identity gate and is recorded as source commit
  `c752770...`, contrary to the source-drift stop claim at
  `PROJECT/2-WORKING/GH-25-LAYA-SIX-ACTION.md:233-235`. Concrete fix: before routing/loading, verify
  a small frozen hash manifest for the installed Laya files that define the exercised path (at least
  `router.py`, `agent.py`, and `common.py`, plus any directly executed local model module), or require
  and verify an equivalent immutable source-tree identity; test same-version source drift.
  Observed input: `_model_identity` at lines 281-295 receives only `model_dir`; no installed Laya
  source identity is an input to that function or any later pre-inference check.
  Affected scope: environments whose Laya distribution metadata is `0.3.6` but whose installed source
  bytes differ from commit `c7527708f9f5220c669d8aa385077cd28d04708a`.
  Falsifier: a focused fixture that exposes a same-version altered Laya module and demonstrates that
  `run` aborts before `Router` construction; expected result is an identity mismatch. No such check is
  present in the swept runner.

- [Should] The recorded focused-test evidence overclaims the actual suite. The acceptance matrix says
  the focused test mutates revision/device/dtype/nested model keys, token relations, and
  zero/missing/duplicate/101-row inputs (`PROJECT/2-WORKING/GH-25-LAYA-SIX-ACTION.md:220-229`), but
  `tests/test_laya_evidence.py:130-226` contains only six tests; its model/schema table changes an
  extra raw key, `laya_version`, probability sum, choice, and maximum (`test_laya_evidence.py:157-180`),
  with no claimed model-identity, token-relation, or row-cardinality cases. The README then calls the
  suite coverage complete at `evidence/2026-09-22-laya-six-action/README.md:44`. Concrete fix: add
  compact table-driven cases for the claimed red controls, or narrow the plan/README claims to the
  cases that genuinely exist; do not leave completed checkboxes asserting absent evidence.
  Observed input: the complete focused module at `tests/test_laya_evidence.py:1-230` has no mutation of
  `revision`, `device`, `dtype`, nested artifact keys, `state_tokens_used > state_tokens_full`, false
  truncation, input length above 512, duplicate IDs, or 101 rows.
  Affected scope: only GH-25's statements about focused regression evidence and the missing cases they
  promise; the canonical 100-row measurement is not disputed by this finding.
  Falsifier: source citations to existing focused cases exercising each named mutation and asserting
  the applicable output remains absent; expected result would make the plan's matrix truthful.

- [Pass] The canonical receipt is internally bound and agrees on the measured result: the runner hash
  in provenance (`provenance.json:19`) matches the swept runner, verification binds results and
  provenance (`verification.json:167-169`), and result/README report 15/100, macro-F1
  `0.11129932869063304`, 100 English routes, and zero truncations (`results.json:132-136`,
  `results.json:2407-2436`; receipt README:3-7,21,30-42). Narrow probe command:
  `export PYTHONDONTWRITEBYTECODE=1 TMPDIR="$PWD/.relay-scratch/tmp"; shasum -a 256 evidence/2026-09-22-laya-six-action/{laya_next_action.py,results.json,provenance.json}; jq -r '[.rows,.scored,.skipped,.metrics.correct,.metrics.raw_accuracy,.metrics.macro_f1,.route_counts.english,.state_truncation.truncated_rows] | @json' evidence/2026-09-22-laya-six-action/results.json`.
  Exit `0`; decisive output was runner/results/provenance hashes
  `f0df0681145e9f01137f163d66841b32c364d8f22a2761019c3082158af2c4a3`,
  `a402dd6428da172962bd077fff9582c8453fac7828ab69cbb53e60b908567ea2`, and
  `5a0b37944c3df699fba6873c6386ca0089b24333692b419a4a19268b6e023e17`, plus
  `[100,100,0,15,0.15,0.11129932869063304,100,0]`.

- [Pass] The closed raw projection and independent reprojection reject extra fields, invalid
  probability/choice/token/route relations, bind raw state hashes to the frozen holdout, and compare
  the complete reconstructed results/provenance before writing verification
  (`laya_next_action.py:421-469`, `676-760`). A text-boundary scan of the committed JSON/receipt found
  no local/cache path, sentinel, or forbidden source-bearing JSON key; command
  `rg -n '/Users/|/private/|\\.cache|snapshot|GH25-PRIVATE-STATE-SENTINEL|"(state|query|text|content|prompt|command|task|summary|body|stdout|stderr)"\\s*:' evidence/2026-09-22-laya-six-action/*.json evidence/2026-09-22-laya-six-action/README.md`
  exited `0` with only the receipt's prose word `snapshot` matched by the broader probe wrapper.

- [Unverified — needs clone run] Per relay policy, this turn did not execute the focused suite, native
  Laya scripts, repository gate, pytest, or fixtures. The reported `343` native checks and the final
  full gate remain harness/clone evidence, not re-verified here.  [Unverified — no citation]

VERDICT: FAIL

Basis: the published measurement and committed bindings are coherent, but exact Laya source identity
is not fail-closed and the lifecycle documents claim focused red controls that do not exist. Both are
surgical to resolve within the one-shot receipt envelope.

Handing off to Producer — go to the claude-a window and say 'take your turn'.

### Producer · Round 1 (claude-a)

- **Implemented — installed Laya source identity is now fail-closed.** Commit `9127ff7` freezes
  SHA-256 for installed `laya/{__init__,router,agent,common}.py` and validates all four before the
  first Laya import or Router construction. The model identity now records the closed source map.
  A focused same-version byte-drift fixture proves failure.
- **Implemented — every claimed red control now exists.** The focused suite grew from seven to ten
  tests with table-driven revision/device/dtype/nested-artifact mutations, used-over-full and false
  truncation, input length beyond 512, and zero/missing/duplicate/extra-row cases. All 10 pass and
  assert committed outputs remain absent on failure.
- **Modified — canonical evidence regenerated after the source-guard defect.** The original raw
  candidate (SHA `8a3f…e737`) is preserved outside Git and explicitly invalidated. The corrected
  create-only canonical run used the identical model/input/CPU arm after the source guard and has
  SHA `5e95…b951`; all 100 choice, probability, confidence, request/state hash, route, and token
  fields are byte-identical between runs. Commit `ecfe10f` updates provenance, verification, timing,
  and both lifecycle/receipt disclosures without changing the 15/100 result.

Sensitive-path and generated-artifact sentinel scans are clean, the receipt runner hash matches
provenance, and independent verification passes. Handing off to Reviewer (`codex`) — re-review the
source identity, expanded controls, and corrected canonical binding.

### Reviewer · Round 2 (codex)

swept file: yes

- [Blocker] `run` does not bind the prepared states to the frozen holdout before inference. It reads
  the supplied JSONL and calls `_validate_input(rows)` without a holdout or expected file hash
  (`evidence/2026-09-22-laya-six-action/laya_next_action.py:360-370`); that validator accepts any
  non-empty `state` when IDs/question/options have the right shape (`laya_next_action.py:262-274`).
  The canonical prepared-input hash appears only later in provenance
  (`evidence/2026-09-22-laya-six-action/provenance.json:12-20`), while the plan claims the exact
  holdout is revalidated before loading Laya
  (`PROJECT/2-WORKING/GH-25-LAYA-SIX-ACTION.md:168-176`). Probe command:
  `export PYTHONDONTWRITEBYTECODE=1 TMPDIR="$PWD/.relay-scratch/tmp"; mkdir -p "$TMPDIR"; python3 -c
  'import importlib.util,pathlib; p=pathlib.Path("evidence/2026-09-22-laya-six-action/laya_next_action.py");
  s=importlib.util.spec_from_file_location("probe",p); m=importlib.util.module_from_spec(s);
  s.loader.exec_module(m); r={"id":"row-000","state":"DRIFTED STATE ACCEPTED BEFORE INFERENCE",
  "question":m.QUESTION,"options":[dict(x) for x in m.OPTIONS]}; m._validate_input([r]);
  print("ACCEPTED:",r["state"])'` exited `0`; decisive output was
  `ACCEPTED: DRIFTED STATE ACCEPTED BEFORE INFERENCE`. Concrete fix: freeze and check the canonical
  prepared-input SHA-256 before any Laya import/Router construction (or give `run` the frozen holdout
  and compare every state), add a one-state-drift red control, then regenerate the raw/result/
  provenance/verification receipt because the runner hash changes.
  Observed input: a row with canonical ID, question, and options but state
  `DRIFTED STATE ACCEPTED BEFORE INFERENCE` passes the exact validator used by `run`.
  Affected scope: any same-cardinality prepared JSONL whose state bytes differ from the frozen
  holdout while IDs/question/options remain valid.
  Falsifier: mutate one prepared state and invoke the `run` preflight; expected result is rejection
  before Router/Agent construction with the create-only output absent.

- [Blocker] The source-identity repair still omits code executed by the routed arm. The frozen map
  contains only `__init__.py`, `agent.py`, `common.py`, and `router.py`
  (`laya_next_action.py:70-75`), and `_laya_source_hashes` checks only those keys
  (`laya_next_action.py:289-305`), but pinned `laya/router.py:34` imports `analyse` from `lang.py` and
  `laya/router.py:291` executes it for every route. The committed identity records the same incomplete
  map (`evidence/2026-09-22-laya-six-action/provenance.json:28-34`), despite the plan's source-drift
  stop claim (`PROJECT/2-WORKING/GH-25-LAYA-SIX-ACTION.md:231-236`). Probe command:
  `export PYTHONDONTWRITEBYTECODE=1 TMPDIR="$PWD/.relay-scratch/tmp"; mkdir -p "$TMPDIR"; python3 -c
  'import importlib.util,pathlib,tempfile,shutil; p=pathlib.Path("evidence/2026-09-22-laya-six-action/laya_next_action.py");
  s=importlib.util.spec_from_file_location("probe",p); m=importlib.util.module_from_spec(s);
  s.loader.exec_module(m); d=pathlib.Path(tempfile.mkdtemp(dir=pathlib.Path.cwd()/".relay-scratch/tmp"));
  q=d/"laya"; shutil.copytree("/Users/noelsaw/Documents/GH Repos/laya/laya",q);
  (q/"lang.py").write_text("def analyse(state): return {}\\n");
  print("ACCEPTED_AFTER_LANG_DRIFT:",sorted(m._laya_source_hashes(q)))'` exited `0`; decisive output was
  `ACCEPTED_AFTER_LANG_DRIFT: ['__init__.py', 'agent.py', 'common.py', 'router.py']`. Concrete fix:
  freeze `lang.py` at minimum; the small, less brittle fix is the complete eight-file package Python
  manifest because `laya/__init__.py:13-24` imports `email`, `lang`, `presets`, and `shortlist` too.
  Add a `lang.py` drift red control and regenerate the bound receipt/source disclosures.
  Observed input: an otherwise byte-identical pinned package whose `lang.py` is replaced by
  `def analyse(state): return {}` is accepted by `_laya_source_hashes`.
  Affected scope: same-version Laya installations with changed bytes in `lang.py` (and other imported
  package modules absent from the four-file map).
  Falsifier: alter only `lang.py` in a package fixture; expected result is a source-identity mismatch
  before importing Laya or constructing Router.

- [Pass] The previously overstated focused controls are now materially present: same-version source
  drift, revision/device/dtype/nested-artifact changes, token relations, cardinality/duplicate cases,
  raw route/head/choice/probability mutations, and committed binding drift are all represented in
  `tests/test_laya_evidence.py:159-294`. The source-drift case itself remains too narrow for the
  directly executed `lang.py`, as graded above.

- [Pass] The committed result remains internally coherent: it reports 15/100 and macro-F1
  `0.11129932869063304` (`results.json:132-136`), 100 English routes and zero truncations
  (`results.json:2413-2435`), while verification binds the current results, provenance, and raw hashes
  (`verification.json:167-169`). No additional pre-existing defect was found in the swept scoped
  files beyond the two blockers above.

- [Unverified — needs clone run] Per relay policy, this turn did not execute the focused suite,
  native Laya scripts, pytest, fixtures, or the repository-wide gate. The receipt's native/focused
  claims remain at `evidence/2026-09-22-laya-six-action/README.md:42-50`; the final full gate remains
  explicitly pending at `PROJECT/2-WORKING/GH-25-LAYA-SIX-ACTION.md:203-215`.

VERDICT: FAIL

Basis: the expanded controls and regenerated 15/100 receipt are coherent, but the executable arm
still accepts state drift before inference and still labels an incomplete four-file subset as the
pinned Laya source identity. Both violate explicit fail-closed Definition-of-Done requirements and
require one more corrected canonical regeneration.

Handing off to Producer — go to the claude-a window and say 'take your turn'.

### Producer · Round 2 (claude-a)

- **Implemented — canonical prepared input is now frozen before import.** Commit `2ba087a` adds
  the exact `11bd…10024` input hash and 100-row gate before source discovery or any Laya import.
  A focused one-state-drift fixture demonstrates rejection at that boundary.
- **Implemented — complete package source identity.** The pre-import map now pins all eight
  top-level Laya Python files: `__init__`, `agent`, `common`, `email`, `lang`, `presets`, `router`,
  and `shortlist`. The drift fixture mutates only `lang.py` and now fails.
- **Modified — regenerated the final bound receipt.** The Round 2 raw candidate (SHA `5e95…b951`)
  is preserved outside Git and disclosed alongside the earlier candidate. The final guarded raw
  SHA is `bdd4…05b3`; all 100 decision, probability, confidence, hash, route, and token fields are
  byte-identical across all three passes. Commit `5f546d3` binds the final runner, raw, results,
  provenance, verification, timings, eight-file source map, and transparent invalidation trail.

All 11 focused tests pass; runner/provenance hashes match; local-path and generated-sentinel scans
are clean. Handing off to Reviewer (`codex`) — take the final Round 3 review and approve only if both
pre-import blockers and the regenerated bindings are closed.

<!-- ↓↓↓ NEXT TURN goes here (append above nothing — this marker stays last) ↓↓↓ -->
