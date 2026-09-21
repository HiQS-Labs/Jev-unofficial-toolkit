# Marathon Phase human_protocol
STATUS: Open
NEXT: codex (Builder)

<!-- marathon-drive: task=MARATHON-HUMAN_PROTOCOL-TURN builder=codex reviewer=agy round-cap=5 -->

## Phase Brief

# Human-reference protocol phase — GH-10

Draft only `HUMAN-LABEL-PROTOCOL.md` on the current branch, using issue #10, its inbox capture, PROTOCOL.md, USE-CASES.md and the frozen receipt evidence. Define a prospective public-data population, rare-class coverage, trained independent human labelers, blinding, adjudication, uncertain rows, class support, metrics, a pre-registered confidence gate, commitments, privacy, and a stop rule. State on this page that the published classification labels are a three-model consensus, not human gold. Distinguish protocol readiness from an actual human-reference result.

Do not claim to be a human labeler or run live Jev calls. Do not include source issue titles or descriptions, secrets or private local paths. Run only the offline documentation/fixture checks. Leave issue #10 open for the actual human-label experiment.


---

▶ TAKE YOUR TURN (codex — BUILDER role)

You are the BUILDER for this phase. Read the phase brief above and implement it.
APPEND-ONLY FILE (GH-529 attestation): add your block at the END and never delete, reorder, or rewrite any existing content — the terminal attestation refuses the approval if any byte above your block changed, even a tidy-up.
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
APPEND-ONLY FILE (GH-529 attestation): add your block at the END and never delete, reorder, or rewrite any existing content — the terminal attestation refuses the approval if any byte above your block changed, even a tidy-up.
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
