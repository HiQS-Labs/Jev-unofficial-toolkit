# RELAY · GH-22 SemIf six-action final QA
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

<!-- ↓↓↓ NEXT TURN goes here (append above nothing — this marker stays last) ↓↓↓ -->
