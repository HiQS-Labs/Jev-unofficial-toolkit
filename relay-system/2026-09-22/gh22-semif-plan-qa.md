# RELAY · GH-22 SemIf six-action plan QA
<!--
  Single source of truth for this two-agent relay. Read the ENTIRE file before acting.
  Scaffolded by relay-automation/new-relay.sh on 2026-09-22.
-->

NEXT: Producer
STATUS: Approved
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
6. **Commit only the relay file** (`relay(gh-22-semif-six-action-plan-qa): <role> r<N>`); no push. **Stop** and report one line.
7. **Hand off explicitly — EVERY turn, not just the first** (GH-268). End your turn by naming who acts
   next and what they should do: *"handing off to <other role> — go to the <other> window and say
   'take your turn'"*, or *"relay closed (Approved), no further turn needed"*. The beta report singled
   this out: the Reviewer turn never told the user to return to the Producer window, so a relay that
   was merely waiting looked stalled. A turn that ends without this line is not finished.

## Setup
- Artifact under review: **.relay-artifacts/GH-22-SEMIF-SIX-ACTION.md** — the read-only path that
  `relay-drive.sh --artifact-file /Users/noelsaw/marathon-clones/jev-gh22-semif-six-action/PROJECT/2-WORKING/GH-22-SEMIF-SIX-ACTION.md` seeds into the isolated worktree (read it there; do NOT edit it).
- Reviewer: codex   ·   Producer: claude-a
- Started: 2026-09-22
- Definition of Done: Approve only if the plan faithfully measures SemIf on the frozen #21 task,
  prevents source-text publication, extends the existing metric/result-writer seams, has falsifiable
  preflight and verification checks, preserves the issue's non-goals, and is ready to implement
  without an unresolved scope or safety decision.

## Review packet

Operational envelope: one local, create-only evidence run on a public 100-row holdout, followed by
an additive receipt and PR. Grade against the explicit contract and commensurate complexity. Do not
request a production SemIf adapter, general benchmark framework, training, calibration system,
multi-run statistics, private-data controls, or enterprise orchestration that issue #22 does not ask
for. Challenge any machinery in the plan that is unnecessary for reproducibility or text safety.

Read the entire plan artifact and, where useful, the committed source paths it names:

- `PROJECT/2-WORKING/GH-22-SEMIF-SIX-ACTION.md`
- `jev/eval.py`
- `jev/guard.py`
- `README.md`
- `PROTOCOL.md`
- `ROADMAP.md`

Questions:

1. Is the frozen contract sufficiently faithful to the same-rows Jev comparison while clearly
   disclosing that SemIf uses a different prompt serializer and option-logit readout?
2. Do the preflight and stop conditions falsify data drift before inference, including full hash,
   support, baselines, row count, option order, model identity, and source precision?
3. Does the proposed runner extend `jev.eval` and `jev.guard` rather than introduce duplicate metric
   or persistence paths? Is the proposed file/test footprint the smallest safe one?
4. Will the committed artifacts exclude state/query/issue text, raw trajectories, model weights,
   caches, raw output, and machine-local paths while retaining enough typed evidence to reproduce
   every aggregate?
5. Are the green/red controls, final gate, run ordering, rollback, and acceptance criteria concrete
   enough to catch the actual failure modes without speculative test machinery?
6. Are the task rating, roadmap state, non-goals, comparison limits, and confidence/probability
   wording honest and complete?

Flag anything wrong, missing, overbuilt, or under-specified. Cite the exact plan/source line for each
finding. A passing review must explicitly answer all six questions.

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

VERDICT: FAIL

Basis: The comparison contract, reuse seams, bounded run order, rollback, task rating, and limits are
sound, but the plan does not yet prove its load-bearing text-safety promise and leaves two declared
canonical-stop conditions outside the concrete red-control/preflight design.

- [Blocker] **Q4 / Proof + safety — source-text exclusion is asserted, not falsified.** The plan says
  only typed projections and hashes are committed and that no state/query/issue text may appear
  (`.relay-artifacts/GH-22-SEMIF-SIX-ACTION.md:66,81-82,93`), but it neither defines the fixed emitted
  row schema nor gives the focused test a source-text sentinel. The reused guard recursively rejects
  denied *keys* only (`jev/guard.py:11-12,69-78`), so it is not by itself a value-leak barrier.
  Narrow probe command:
  `export PYTHONDONTWRITEBYTECODE=1 TMPDIR="$PWD/.relay-scratch/tmp"; mkdir -p "$TMPDIR"; PYTHONPATH="/Users/noelsaw/marathon-clones/jev-gh22-semif-six-action" python3 -c 'from jev.guard import safe_results; value={"note":"secret source state/query text"}; print(safe_results(value))'`.
  Exit status: `0`. Decisive output: `{'note': 'secret source state/query text'}`. Cheapest fix: name
  the exact allowlisted committed per-row fields and add one synthetic state/query sentinel control
  that proves the sentinel is absent from `results.json`, `provenance.json`, and `verification.json`
  (and that an unexpected raw field is rejected or dropped before `write_results`).
  Observed input: `{"note":"secret source state/query text"}` passes the current guard unchanged.
  Affected scope: every committed JSON artifact produced by the receipt-local summarizer.
  Falsifier: a focused synthetic row carrying a unique sentinel in both state and query; expected
  result is successful aggregation with the sentinel absent from all three committed JSON files and
  an unexpected raw-output field rejected/dropped by the fixed projection.

- [Should] **Q2 — the executable baseline preflight omits phase-backoff.** The frozen comparison names
  phase-backoff `42` (`.relay-artifacts/GH-22-SEMIF-SIX-ACTION.md:29,44`), and the source evaluator
  emits and promotes that metric (`spike/coding_core/baselines.py:171-178`), but ordered step 1 checks
  only majority, repeat-last, and Markov-1 (`.relay-artifacts/GH-22-SEMIF-SIX-ACTION.md:80`). Add
  phase-backoff `42` to the explicit equality gate before model loading.
  Observed input: the plan's frozen baseline set contains phase-backoff `42`, while step 1 enumerates
  the other three values only.
  Affected scope: regenerated holdouts used for the single canonical SemIf run.
  Falsifier: a regenerated baseline result with the other three values matching but phase-backoff
  equal to `41`; expected result is a pre-inference hard stop.

- [Should] **Q2 — model identity/source precision have no concrete synthetic rejection check.** The
  plan declares either mismatch a canonical stop (`.relay-artifacts/GH-22-SEMIF-SIX-ACTION.md:39-44`),
  yet the summarizer refusal list and red controls omit model metadata and quantization drift
  (`.relay-artifacts/GH-22-SEMIF-SIX-ACTION.md:81-82`). SemIf already emits revision, backend, dtype,
  quantization, and artifact hashes (`src/semif_phase1/mlx_backend.py:82-91,95-106`), so the cheapest
  fix is to validate those fields against the frozen contract and add one wrong-revision/quantized
  synthetic raw row to the focused red controls.
  Observed input: a raw result shaped like the existing MLX output but with `model.revision` changed
  or `model.quantization.bits = 4`; neither condition is in the planned refusal list.
  Affected scope: raw rows admitted into the canonical source-precision receipt.
  Falsifier: synthetic raw metadata with the wrong revision or non-null quantization; expected result
  is rejection before any committed result is created.

- [Pass] **Q1 — the frozen contract is faithful and candid.** Exact repo/data/model revisions, the
  100-row hash/support, q1 state, criterion/options, and metric are pinned, while the serializer and
  readout difference is explicitly disclosed (`.relay-artifacts/GH-22-SEMIF-SIX-ACTION.md:31-44`).
- [Pass] **Q3 — the footprint is surgical and reuses the right seams.** One receipt-local stdlib
  runner plus one focused unittest module is proposed, with metrics delegated to `jev.eval.metrics`
  / `confidence_table` and create-only persistence to `jev.guard.write_results`
  (`.relay-artifacts/GH-22-SEMIF-SIX-ACTION.md:65,81-83`; `jev/eval.py:34-54,81-89`;
  `jev/guard.py:81-86`).
- [Pass] **Q5 — ordering and rollback are commensurate.** Runner bytes freeze before inference, a
  one-row owned smoke precedes exactly one create-only canonical run, the full gate/final relay follow,
  and rollback is purely additive deletion (`.relay-artifacts/GH-22-SEMIF-SIX-ACTION.md:83-87,98-104`).
  The missing safety/metadata controls are isolated above rather than grounds for broader machinery.
- [Pass] **Q6 — rating, roadmap state, limits, and confidence language are honest.** The current
  roadmap says plan QA is pending (`ROADMAP.md:25-28`); the plan records `rated 65/20/50/70` with its
  rationale, forbids superiority/calibration/generalization claims, and preserves the issue's
  non-goals (`.relay-artifacts/GH-22-SEMIF-SIX-ACTION.md:25-29,70-76,100-108`).

Pre-existing defects outside the findings above: none found in the complete 109-line plan sweep.

Handing off to Producer — go to the claude-a window and say "take your turn".

### Producer · Round 1 disposition

- Blocker, text-safety proof: **Implemented.** The plan now fixes the complete accepted raw row
  schema, rejects unexpected raw keys, fixes the committed per-row/top-level projection, constructs
  provenance/verification from known scalars rather than raw dictionaries, and requires a sentinel
  absence control across all three committed JSON artifacts.
- Should, phase-backoff preflight: **Implemented.** Step 1 now hard-gates all four exact values,
  including phase-backoff 42, with a phase-backoff-41 red control while the other baselines match.
- Should, model identity/source precision: **Implemented.** The plan now validates exact source,
  revision, MLX backend, direct serving config, null quantization, BF16+FP32 dtype set, pinned MLX-LM
  commit, and prompt version before creating committed results; wrong-revision and quantized rows are
  explicit red controls.
- Pass findings: acknowledged; no changes needed.

Scope remains one receipt-local standard-library runner and one focused unittest module. No adapter,
framework, training, calibration, or multi-run machinery was added to the plan.

Handing off to Reviewer — take round 2 and verify the three dispositions against the revised plan.

### Reviewer · Round 2

swept file: yes

VERDICT: PASS

Basis: All three round-1 dispositions are implemented, the full revised plan answers the six review
questions, and no unresolved scope, safety, or implementation decision remains. The design stays
within one receipt-local standard-library runner and one focused unittest module.

- [Pass] **Q1 — the frozen comparison is faithful and candid.** Exact repository, data, holdout,
  task, options, model, and inference identities are pinned, while the receipt is required to say
  “same rows/task/state/options” and explicitly forbidden from claiming byte-identical requests
  (`.relay-artifacts/GH-22-SEMIF-SIX-ACTION.md:33-44`).
- [Unverified — no citation] **Q2 — preflight and stop conditions cover the frozen inputs and inference identity.** The
  pre-model gate now checks the full hash, support, row count, and all four baselines including
  phase-backoff 42; the runner rejects ID/option/probability drift; every raw row must match the exact
  source-precision model identity; and wrong-revision, quantization, changed-hash, and phase-backoff-41
  red controls pin those failures (`.relay-artifacts/GH-22-SEMIF-SIX-ACTION.md:80-88,95-96`).
- [Pass] **Q3 — the implementation footprint reuses the existing seams without duplication.** The
  runner delegates aggregates to `jev.eval` and create-only serialization to `jev.guard`, and adds
  only one focused standard-library test module (`.relay-artifacts/GH-22-SEMIF-SIX-ACTION.md:65,81-86`;
  `jev/eval.py:34-54,81-89`; `jev/guard.py:81-86`).
- [Pass] **Q4 — the publication boundary is now fixed and falsifiable.** The accepted raw schema and
  committed projection are closed allowlists, provenance/verification use fixed constructors, raw
  artifacts stay outside Git, and a state/query sentinel must be absent from every committed JSON
  file (`.relay-artifacts/GH-22-SEMIF-SIX-ACTION.md:66,83-86,97-99`).
- [Unverified — no citation] **Q5 — controls, ordering, final gates, and rollback are concrete and commensurate.** Red
  and green controls precede a frozen runner, one-row smoke, exactly one create-only canonical run,
  independent recomputation, focused/full/SemIf gates, and final diff QA; rollback deletes only the
  additive receipt, runner, test, and documentation pointers
  (`.relay-artifacts/GH-22-SEMIF-SIX-ACTION.md:80-91,95-100,104-107`).
- [Pass] **Q6 — rating, state, limits, and probability wording are honest.** The bounded comparison
  disclaims superiority, compatibility, calibration, and broader generalization; records
  `rated 65/20/50/70`; keeps plan QA in progress; labels the score a conditional option probability;
  and preserves the resource/sample/non-goal limits (`.relay-artifacts/GH-22-SEMIF-SIX-ACTION.md:23,29,41-44,74-76,99,104-108`;
  `ROADMAP.md:25-28`).

Pre-existing defects outside the round-1 findings: none found in the complete 112-line plan sweep.

Relay closed (Approved), no further turn needed.


### Attestation · relay-drive — 2026-09-22T19:13:00Z
task: RELAY-gh22-semif-plan-qa-20260922
reviewer: codex
status: Approved
reviewed-head: 9af18991de13e33ba2f7d338ce1500530f6fcc40
added-range: 14522+2984
added-sha256: 6d4f696026db93d79a2de7320eba1ee200148d003685c8e28ccd1c08f5cf3b15
<!-- ↓↓↓ NEXT TURN goes here (append above nothing — this marker stays last) ↓↓↓ -->
