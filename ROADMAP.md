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
| #6 recovery and #9 OpenRouter access merged in PR #19; #12 harness prerequisites merged in PR #20. | Finalize and separately authorize #10's prospective human-reference experiment; continue #13–#15 only with task-specific evidence. |

## Ledger

### Queue / parked intake

- [GH-10 human-label validation](PROJECT/1-INBOX/GH-10-HUMAN-LABELS.md) — needs an independent human reference and authorized sample.

### In progress

- [GH-11 starter readiness](PROJECT/2-WORKING/GH-11-STARTER-READINESS.md) — transport work is complete; the umbrella remains open for #10's separately authorized human-reference receipt.
- [GH-25 Laya six-action comparison](PROJECT/2-WORKING/GH-25-LAYA-SIX-ACTION.md) — PR ready; awaiting merge in [#27](https://github.com/HiQS-Labs/Jev-unofficial-toolkit/pull/27) with the canonical 15/100 receipt, final Codex QA, and green local/hosted gates.

### Completed

- [GH-26 GPT-6 Luna comparison](PROJECT/2-WORKING/GH-26-GPT6-LUNA-SUBAGENTS.md) — authorized fresh-CLI rerun completed 30/100 on its first attempt; original failed subagent pass retained unscored.

- [GH-22 SemIf six-action comparison](PROJECT/2-WORKING/GH-22-SEMIF-SIX-ACTION.md) — merged in PR #24 with canonical 24/100 receipt, final Codex QA, and green local/hosted gates.
- [GH-6 live answer recovery](PROJECT/2-WORKING/GH-6-PROBABILITY-CHECKPOINTS.md) — closed after checkpoint and optional-probability recovery shipped in PR #19.
- [GH-9 OpenRouter access](PROJECT/2-WORKING/GH-9-OPENROUTER-ACCESS.md) — closed after the pinned Decisions adapter and mock coverage shipped in PR #19.
- GH-12 judgment harness prerequisites — closed after Score/Noul scoring, schema validation, policy composition, and decision logging shipped in PR #20. No local project doc was created for this issue.

### Deferred

- No deferred docs.

---

*Add new work here only when a real `PROJECT/**` doc exists to own the execution detail.*
