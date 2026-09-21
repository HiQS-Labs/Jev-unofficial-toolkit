<!-- PDDA ROADMAP CONTRACT — this file is a POINTER/LEDGER, not a plan body.
     Allowed: queued intake / projects in progress / completed / attempted / deferred + links to PROJECT/** docs.
     NOT allowed: phase checklists, build steps, deep execution notes — put those in the project doc.
     Carve-out: a SHORT exception note is OK only when omitting it would hide an operationally critical fact.
     Coverage rule: every PROJECT/2-WORKING doc must be reflected here by a pointer (or opt out with roadmap_exempt: true).
     Enforced by `pdda.sh roadmap` + `pdda.sh roadmap-coverage` (deterministic) + utils/pdda/pdda-doc-ready.sh ROADMAP rubric (LLM). -->

# Roadmap

> **Pointer/ledger only — not a plan body.** Execution detail (phase checklists, build steps, QA
> gates, deep notes) lives in the linked `PROJECT/**` docs; keep it there. See the contract banner above.

## Status

| What was just completed | What's next |
|---|---|
| #6 recovery, #9 OpenRouter adapter, and #10 protocol draft completed on one branch. | Review and merge the starter-readiness PR; later authorize a separate human-reference experiment. |

## Ledger

### Queue / parked intake

- [GH-10 human-label validation](PROJECT/1-INBOX/GH-10-HUMAN-LABELS.md) — needs an independent human reference and authorized sample.

### In progress

- [GH-6 live answer recovery](PROJECT/2-WORKING/GH-6-PROBABILITY-CHECKPOINTS.md) — fix committed on the starter branch, awaiting review.
- [GH-11 starter readiness](PROJECT/2-WORKING/GH-11-STARTER-READINESS.md) — one-branch marathon tracking #6, #9 and #10 protocol.
- [GH-9 OpenRouter access](PROJECT/2-WORKING/GH-9-OPENROUTER-ACCESS.md) — reviewed implementation awaiting PR merge.

### Completed

- No completed docs.

### Deferred

- No deferred docs.

---

*Add new work here only when a real `PROJECT/**` doc exists to own the execution detail.*
