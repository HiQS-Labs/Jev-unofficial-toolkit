# Marathon Phase openrouter
STATUS: Open
NEXT: codex (Builder)

<!-- marathon-drive: task=MARATHON-OPENROUTER-TURN-2 builder=codex reviewer=agy round-cap=5 -->

## Phase Brief

# OpenRouter phase — GH-9

Implement #9 on the current `feat/11-starter-readiness` branch only. Read the exact issue, `GH-9-OPENROUTER-ACCESS.md`, the existing client/CLI/answers/tests and the TypeSafe/OpenRouter primary docs linked in the capture. The endpoint is the dedicated OpenRouter Decisions API, with the versioned `typesafe/jev-1.13` slug; never send a Jev decision to chat completions or the moving latest alias. Keep direct TypeSafe behavior and historical receipts stable. Use the existing stdlib patterns, text-free writer, model checks, hashes, retries and mock-only CI. The #6 checkpointing fix is already committed.

The response contract has already been verified with one operator-authorized synthetic live call; do not make another call. POST `https://openrouter.ai/api/alpha/decisions` with requested model `typesafe/jev-1.13` returned HTTP 200, concrete response model `typesafe/jev-1.13-20260917`, provider `TypeSafe`, top-level fields `answers,id,model,provider,usage`, answer fields `choice,confidence,probabilities,type`, and usage fields `cost,input_tokens,output_tokens`. The request/response SHA-256 hashes are `3a6edcb2828bf56685674c17077a68baf482e83e3e54f4f3362a79f25d1fbcfe` and `575423d147bd80c27a3ef4a754a67079e491471e9e8b06610dcbe610737d0177`. This verifies the typed contract without retaining raw state/response or key. Implement the adapter now from these facts. Never print, commit or paste the key, raw response body, source issue text or local secret path. Do not spend on a historical benchmark.

Run the focused mock suite and keep the output in the existing one-branch PR. Agy review must assess code and evidence; do not claim human approval or a performance gain.


---

▶ TAKE YOUR TURN (codex — BUILDER role)

You are the BUILDER for this phase. Read the phase brief above and implement it.
APPEND-ONLY FILE (GH-529 attestation): add your block at the END and never delete, reorder, or rewrite any existing content — the terminal attestation refuses the approval if any byte above your block changed, even a tidy-up.
1. Implement the brief by creating/editing the artifact file(s): jev/openrouter.py,jev/cli.py,jev/answers.py,tests/test_jev_harness.py,README.md
2. Append a build block to this relay file: `### Round N · Builder · codex` summarizing what you did (files touched, key decisions).
3. Use this exact tick binary (run it from any directory): /Users/noelsaw/marathon-clones/marathon-gh-11-starter-readiness/.xyz/bin/tick
   - /Users/noelsaw/marathon-clones/marathon-gh-11-starter-readiness/.xyz/bin/tick claim MARATHON-OPENROUTER-TURN-2 --agent codex --paths "marathon-system/gh-11-starter-readiness--openrouter/RELAY.md,jev/openrouter.py,jev/cli.py,jev/answers.py,tests/test_jev_harness.py,README.md"
   - /Users/noelsaw/marathon-clones/marathon-gh-11-starter-readiness/.xyz/bin/tick ping MARATHON-OPENROUTER-TURN-2 --agent codex
   - /Users/noelsaw/marathon-clones/marathon-gh-11-starter-readiness/.xyz/bin/tick release MARATHON-OPENROUTER-TURN-2 --agent codex --to agy
4. Edit ONLY these paths: marathon-system/gh-11-starter-readiness--openrouter/RELAY.md and jev/openrouter.py,jev/cli.py,jev/answers.py,tests/test_jev_harness.py,README.md. Do NOT run git. Do NOT touch any other file — the harness commits for you.
5. HAND OFF EXPLICITLY (GH-268): after releasing the token, end your turn by naming who acts next —
   "handing off to agy — agy, take your turn." A turn that ends without that line
   leaves a human guessing whether the relay is waiting on them or has stalled. Do this EVERY round,
   not just the first. ALSO, you MUST update the `NEXT:` line at the top of this file to exactly: `NEXT: agy (Reviewer)`

---

▶ TAKE YOUR TURN (agy — REVIEWER role)

You are the REVIEWER for this phase. Read the latest builder block above AND review the artifact file(s) on disk: jev/openrouter.py,jev/cli.py,jev/answers.py,tests/test_jev_harness.py,README.md. REVIEW THE WHOLE FILE, NOT JUST THE DIFF (GH-268): a beta test had this loop reach 'Approved' in two rounds while an independent audit of the same branch found 20 issues (1 critical, 4 high) — every one of them in the pre-existing code the change sat on, which nobody had read. Pre-existing defects in a file you are touching are IN SCOPE; say so explicitly if you find none. DECLARE IT: your review block MUST contain a literal 'swept file: yes' or 'swept file: no' line — without it a reviewer that skipped the sweep is indistinguishable in the transcript from one that did it and found nothing, which is exactly how those 20 issues stayed invisible.
APPEND-ONLY FILE (GH-529 attestation): add your block at the END and never delete, reorder, or rewrite any existing content — the terminal attestation refuses the approval if any byte above your block changed, even a tidy-up.
1. Append a review block: `### Round N · Reviewer · agy` followed by your assessment.
2. If changes needed: add `**Verdict:** Changes requested`, update the `NEXT:` line to exactly `NEXT: codex (Builder)`, then: /Users/noelsaw/marathon-clones/marathon-gh-11-starter-readiness/.xyz/bin/tick release MARATHON-OPENROUTER-TURN-2 --agent agy --to codex
3. If satisfied: add `**Verdict:** Approved`, set `STATUS: Approved`, then: /Users/noelsaw/marathon-clones/marathon-gh-11-starter-readiness/.xyz/bin/tick done MARATHON-OPENROUTER-TURN-2 --agent agy
4. Use this exact tick binary (run it from any directory) for all token operations: /Users/noelsaw/marathon-clones/marathon-gh-11-starter-readiness/.xyz/bin/tick
   Edit ONLY marathon-system/gh-11-starter-readiness--openrouter/RELAY.md (your review block + STATUS). Do NOT edit the artifact yourself — request changes instead. Do NOT run git.
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
