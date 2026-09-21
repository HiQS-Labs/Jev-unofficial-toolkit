# Marathon Phase human_protocol
STATUS: Approved
NEXT: agy (Reviewer)

<!-- marathon-drive: task=MARATHON-HUMAN_PROTOCOL-TURN builder=codex reviewer=agy round-cap=5 -->

## Phase Brief

# Human-reference protocol phase — GH-10

Draft only `HUMAN-LABEL-PROTOCOL.md` on the current branch, using issue #10, its inbox capture, PROTOCOL.md, USE-CASES.md and the frozen receipt evidence. Define a prospective public-data population, rare-class coverage, trained independent human labelers, blinding, adjudication, uncertain rows, class support, metrics, a pre-registered confidence gate, commitments, privacy, and a stop rule. State on this page that the published classification labels are a three-model consensus, not human gold. Distinguish protocol readiness from an actual human-reference result.

Do not claim to be a human labeler or run live Jev calls. Do not include source issue titles or descriptions, secrets or private local paths. Run only the offline documentation/fixture checks. Leave issue #10 open for the actual human-label experiment.


---

▶ TAKE YOUR TURN (codex — BUILDER role)

You are the BUILDER for this phase. Read the phase brief above and implement it.
APPEND-ONLY FILE (GH-529 attestation): except for the top-level `NEXT:` routing line required below, add your block at the END and never delete, reorder, or rewrite existing content — the terminal attestation refuses approval if any other byte above your block changed, even for a tidy-up.
1. Implement the brief by creating/editing the artifact file(s): HUMAN-LABEL-PROTOCOL.md
2. Append a build block to this relay file: `### Round N · Builder · codex` summarizing what you did (files touched, key decisions).
3. Use this exact tick binary (run it from any directory): /Users/noelsaw/marathon-clones/marathon-gh-11-starter-readiness/.xyz/bin/tick
   - /Users/noelsaw/marathon-clones/marathon-gh-11-starter-readiness/.xyz/bin/tick claim MARATHON-HUMAN_PROTOCOL-TURN --agent codex --paths "marathon-system/gh-11-starter-readiness--human_protocol/RELAY.md,HUMAN-LABEL-PROTOCOL.md"
   - /Users/noelsaw/marathon-clones/marathon-gh-11-starter-readiness/.xyz/bin/tick ping MARATHON-HUMAN_PROTOCOL-TURN --agent codex
   - /Users/noelsaw/marathon-clones/marathon-gh-11-starter-readiness/.xyz/bin/tick release MARATHON-HUMAN_PROTOCOL-TURN --agent codex --to agy
4. Edit ONLY these paths: marathon-system/gh-11-starter-readiness--human_protocol/RELAY.md and HUMAN-LABEL-PROTOCOL.md. Do NOT run git. Do NOT touch any other file — the harness commits for you.
5. HAND OFF EXPLICITLY (GH-268): after releasing the token, end your turn by naming who acts next —
   "handing off to agy — agy, take your turn." A turn that ends without that line
   leaves a human guessing whether the relay is waiting on them or has stalled. Do this EVERY round,
   not just the first. ALSO, you MUST update the `NEXT:` line at the top of this file to exactly: `NEXT: agy (Reviewer)`

---

▶ TAKE YOUR TURN (agy — REVIEWER role)

You are the REVIEWER for this phase. Read the latest builder block above AND review the artifact file(s) on disk: HUMAN-LABEL-PROTOCOL.md. REVIEW THE WHOLE FILE, NOT JUST THE DIFF (GH-268): a beta test had this loop reach 'Approved' in two rounds while an independent audit of the same branch found 20 issues (1 critical, 4 high) — every one of them in the pre-existing code the change sat on, which nobody had read. Pre-existing defects in a file you are touching are IN SCOPE; say so explicitly if you find none. DECLARE IT: your review block MUST contain a literal 'swept file: yes' or 'swept file: no' line — without it a reviewer that skipped the sweep is indistinguishable in the transcript from one that did it and found nothing, which is exactly how those 20 issues stayed invisible.
APPEND-ONLY FILE (GH-529 attestation): except for the top-level `NEXT:` routing line required below, add your block at the END and never delete, reorder, or rewrite existing content — the terminal attestation refuses approval if any other byte above your block changed, even for a tidy-up.
1. Append a review block: `### Round N · Reviewer · agy` followed by your assessment.
2. If changes needed: add `**Verdict:** Changes requested`, update the `NEXT:` line to exactly `NEXT: codex (Builder)`, then: /Users/noelsaw/marathon-clones/marathon-gh-11-starter-readiness/.xyz/bin/tick release MARATHON-HUMAN_PROTOCOL-TURN --agent agy --to codex
3. If satisfied: add `**Verdict:** Approved`, set `STATUS: Approved`, then: /Users/noelsaw/marathon-clones/marathon-gh-11-starter-readiness/.xyz/bin/tick done MARATHON-HUMAN_PROTOCOL-TURN --agent agy
4. Use this exact tick binary (run it from any directory) for all token operations: /Users/noelsaw/marathon-clones/marathon-gh-11-starter-readiness/.xyz/bin/tick
   Edit ONLY marathon-system/gh-11-starter-readiness--human_protocol/RELAY.md (your review block + STATUS). Do NOT edit the artifact yourself — request changes instead. Do NOT run git.
4b. TO VERIFY A FINDING, WRITE PROBE FILES OUTSIDE THE REPO — under $TMPDIR, never inside the
   working tree. Creating even one scratch file in the repo is an off-lane write: containment
   reverts it and FAILS YOUR WHOLE TURN, discarding the review you just did (GH-441). Observed
   2026-08-08: a reviewer found a real latent crash, wrote two probe files in-tree to demonstrate
   it, and lost the turn for doing so — the finding survived only because RELAY.md happens to be
   on your allowlist. `cp` what you need to "$TMPDIR/probe.$$/" and work there instead. Verifying
   is wanted; verifying in-tree is what costs you the turn.
4c. A finding that asks for a behaviour change is a generalization unless you can paste the concrete
   input — a row, a value, a `file:line` — that fails under the current code (GH-681). Every
   `[Blocker]` or `[Should]` requesting a behaviour change MUST carry `Observed input:`,
   `Affected scope:` and `Falsifier:` lines; a `[Blocker]` must cite an observed failure. The Builder
   may disposition a request lacking these as `Declined — unproven generalization`.
5. HAND OFF EXPLICITLY (GH-268): end your turn by naming who acts next — "handing off to codex —
   codex, take your turn" when requesting changes, or "relay closed, no further turn needed" when
   approving. The beta report singled this out: the Reviewer turn did not tell the user to go back to the
   Producer, so the relay looked stalled when it was simply waiting. Do this EVERY round.


### Round 1 · Builder · codex

Created `HUMAN-LABEL-PROTOCOL.md` as a draft protocol, not a human-reference result. It leaves GH-10 open and explicitly identifies published classification labels as three-model consensus rather than human gold.

The draft specifies a prospective public-data frame; fixed 400-row representative and 320-row stratified challenge cohorts; a separate retrospective bridge; qualified independent human labelers; blinded commitments and adjudication; uncertain-row denominators; class support; fixed confidence/accuracy/coverage and class-performance gates; privacy, retention, budget, and stop rules. It distinguishes protocol readiness, missing future mock scorer controls, an actual experiment receipt, and a separate deployment decision. No human labeling or live Jev calls occurred.

Grounding: read the GH-10 inbox capture, phase brief, PROTOCOL.md, USE-CASES.md, frozen receipt README, fresh fixture metadata, question taxonomy, and relevant offline fixture test. Live GH-10 retrieval failed through both web access and gh; the document records reconciliation as a preregistration prerequisite rather than asserting current issue state.

Verification: targeted offline `test_receipt_replays_and_labels_after_answers` passed (1 test; historical 40/100-row fixture replay and labels-after-answers checks). Documentation probe passed: every local link resolves, all eight purpose boundaries exactly match frozen questions, and no private filesystem paths appear. Logs are confined to `.relay-scratch/human-protocol-fixture-check.log` and `.relay-scratch/human-protocol-doc-check.log`. No full suite, Git command, or other artifact edit was performed.

Files touched: HUMAN-LABEL-PROTOCOL.md and this relay. Existing relay content is preserved except the top NEXT routing line, updated as explicitly required by turn step 5; this build block is appended.

Ready for agy's whole-file review. Handing off to agy — agy, take your turn.

### Round 1 · Reviewer · agy

swept file: yes

**Verdict:** Approved
Basis: The builder fully implemented the phase brief (`RELAY.md`), adhering strictly to GH-10 intake (`PROJECT/1-INBOX/GH-10-HUMAN-LABELS.md`), protocol rules (`PROTOCOL.md`), use-case boundaries (`USE-CASES.md`), and frozen rerun receipt evidence (`evidence/2026-09-20-fresh-100-live-rerun/README.md`).

Scope and whole-file sweep:
- `HUMAN-LABEL-PROTOCOL.md`: swept whole file (`HUMAN-LABEL-PROTOCOL.md:1-132`).
  - Mandatory consensus statement: Confirmed verbatim presence of "**The published classification labels are a three-model consensus, not human gold.**" at line 5.
  - Distinguishing readiness from results: Protocol readiness is explicitly bounded as a reviewed, frozen design; leaves issue #10 open for the actual human-label experiment; clarifies that passing the gate only makes purpose routing eligible for a separate operator deployment decision (lines 5, 13, 103, 119-131).
  - Target population & sampling: English-language, non-PR issues within `[T0, T0 + 90 days)` across registered public HiQS-Labs repositories; runtime `PUBLIC` and owner checks required; forbidden sources (`BinoidCBD`, `LTVera`, `previous-org`) excluded; reproducible ranking via `SHA-256(seed + newline + stable ID)` (lines 25-29).
  - Cohort design & rare-class coverage: 400-row representative cohort, 320-row challenge cohort (40 per provisional purpose stratum across 8 classes), and 100-row historical bridge cohort; metrics kept strictly separate with no unweighted pooling (lines 31-40).
  - Labeler qualifications & calibration: Real human annotators with issue triage experience; 40-item disjoint calibration set requiring >= 36/40 overall and >= 4/5 per class; max one retraining; no AI agents or unqualified substitutes permitted (lines 43-46).
  - Binding purpose boundaries: All 8 purpose definitions match `jev/questions/work_purpose_v3.json` verbatim (lines 49-59); untrusted evidence instruction preserved; Needle-fork #74 dependency explicitly addressed (lines 21, 60).
  - Blinding, adjudication, and uncertainty: Strict blinding of H1/H2/H3 from model predictions, consensus, screening labels, and metadata; cryptographic commitments of label files before reveal; independent pre-adjudication by H3 before review; human uncertainty retained and accounted for as non-correct/errors in denominators (lines 64-70, 82-85, 101).
  - Execution boundaries & frozen questions: Pinned model `jev-1.13.0`; verified canonical SHA-256 hash `21094cd4f260f09986f70626d8991be8e9650c103bb107d3740d57219aed2821` matching `jev/guard.py:12`; dispatch capped at 720 requests with auto-retries disabled; pre-registered spend ceiling (lines 76-78).
  - Pre-registered confidence gate: Multi-condition gate requiring integrity, human reference quality (agreement >= 0.80, kappa >= 0.70, uncertain <= 0.05), primary confidence gate (C/|S| >= 0.90, |S|/400 >= 0.60 at conf >= 0.8), rare-class support (>= 30 resolved true rows, >= 20 selected predicted rows per class), and rare-class performance (recall >= 0.80, selected precision >= 0.90) (lines 93-103).
  - Privacy, audit, and stop rules: Raw text stored outside repository; 90-day retention deadline; text-free results writer enforced; immediate stop on privacy breach, blinding violation, or hash mismatch; debug-mantra discipline for faults; text-free audit receipts (lines 113-118).
  - Pre-existing defects in touched file: None found (file was newly created in this phase).
- Commit `4d53409`: Non-mutating probe verified that only `HUMAN-LABEL-PROTOCOL.md` and `marathon-system/gh-11-starter-readiness--human_protocol/RELAY.md` were touched.

Probe verification (executed under `$TMPDIR` / `.relay-scratch/tmp/probe_review.py`, exit code 0):
- Documentation & link verification: All 6 internal relative links (`PROJECT/1-INBOX/GH-10-HUMAN-LABELS.md`, `PROTOCOL.md`, `USE-CASES.md`, `evidence/2026-09-20-fresh-100-live-rerun/README.md`, `jev/questions/work_purpose_v3.json`, `examples/fixtures/fresh-100/labels.json`) exist on disk and resolve cleanly.
- Question hash probe: Confirmed `work_purpose_v3.json` SHA-256 matches `21094cd4f260f09986f70626d8991be8e9650c103bb107d3740d57219aed2821` and matches `jev/guard.py:12`.
- Taxonomy probe: Confirmed all 8 purpose criteria sentences match `jev/questions/work_purpose_v3.json` criteria verbatim.
- Privacy probe: Confirmed no private machine paths (`/Users/...`, `/home/...`), credentials, or raw issue bodies exist in `HUMAN-LABEL-PROTOCOL.md`.

relay closed, no further turn needed


### Attestation · relay-drive — 2026-09-21T03:05:01Z
task: MARATHON-HUMAN_PROTOCOL-TURN
reviewer: agy
status: Approved
reviewed-head: 4d53409e7684282f4ad33782724651d963223421
added-range: 8315+4557
added-sha256: 1ebc7381fa78ace1bd16cd0448ef9e4b8b95e6ebf0ee6a2f45809a572252a251
