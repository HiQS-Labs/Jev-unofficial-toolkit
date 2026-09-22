# RELAY · GH-22 SemIf six-action plan QA
<!--
  Single source of truth for this two-agent relay. Read the ENTIRE file before acting.
  Scaffolded by relay-automation/new-relay.sh on 2026-09-22.
-->

NEXT: Reviewer
STATUS: Open
ROUND: 1 / 3

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

<!-- ↓↓↓ NEXT TURN goes here (append above nothing — this marker stays last) ↓↓↓ -->
