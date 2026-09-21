---
gh_issue: 11
source: https://github.com/HiQS-Labs/Jev-unofficial-toolkit/issues/11
title: Starter readiness marathon
status: In progress
created: 2026-09-20
updated: 2026-09-20
owner: toolkit maintainer
goal: Resolve the observed live-batch defect, provide a verified OpenRouter path, and prepare independent human-label validation.
doc_type: project
effort: 4
complexity: 4
risk: 2
phases: 2
---

# GH-11 — starter readiness

## Status

| What was just completed | What's next |
|---|---|
| #6 fix committed; #9 adapter and #10 protocol reviewed by Agy; 25 offline tests pass. | Open the one-branch PR and keep #10 open for actual human labeling. |

## Table of contents

1. [OpenRouter lane](#openrouter-lane)
2. [Human-reference protocol lane](#human-reference-protocol-lane)

## OpenRouter lane

Read `GH-9-OPENROUTER-ACCESS.md` and its primary-source discovery before coding. Implement only the verified typed Decisions API, with exact model and backend identity, safe key loading, mock tests and documentation. #6's checkpointing fix remains in place.

QA: the offline suite passes, no direct-TypeSafe fixture changes, no key or source text in tracked files. A bounded synthetic live check may be run using the operator-provided key path only after the mock lane passes.

## Human-reference protocol lane

Draft an offline human-label plan under #10. The plan must expose sampling, blinding, adjudication, minimum class support, commitment, denominators and advance gate. Treat human labeling and new model calls as an external dependency; the written plan cannot claim human-reference accuracy.

QA: the protocol is self-contained, uses no raw issue text, and explicitly says that existing classification labels are a three-model consensus, not human gold. A later human operation needs its own authorization and receipt.
