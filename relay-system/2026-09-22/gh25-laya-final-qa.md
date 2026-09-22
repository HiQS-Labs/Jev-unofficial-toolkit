# RELAY · GH-25 Laya six-action final implementation QA
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
6. **Commit only the relay file** (`relay(gh25-laya-final-qa): <role> r<N>`); no push. **Stop** and report one line.
7. **Hand off explicitly — EVERY turn, not just the first** (GH-268). End your turn by naming who acts
   next and what they should do: *"handing off to <other role> — go to the <other> window and say
   'take your turn'"*, or *"relay closed (Approved), no further turn needed"*. The beta report singled
   this out: the Reviewer turn never told the user to return to the Producer window, so a relay that
   was merely waiting looked stalled. A turn that ends without this line is not finished.

## Setup
- Artifact under review: the complete `origin/main..b00cde7` implementation diff. Read `evidence/2026-09-22-laya-six-action/`, `tests/test_laya_evidence.py`, `PROJECT/2-WORKING/GH-25-LAYA-SIX-ACTION.md`, `README.md`, and `ROADMAP.md` in full, including committed prediction rows and JSON contracts where material. Ignore this temporary relay transcript itself.
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

<!-- ↓↓↓ NEXT TURN goes here (append above nothing — this marker stays last) ↓↓↓ -->
