---
gh_issue: 11
source: https://github.com/HiQS-Labs/Jev-unofficial-toolkit/issues/11
title: Starter readiness marathon
status: Transport complete; human-reference execution pending
created: 2026-09-20
updated: 2026-09-20
reviewed_after_merge: true
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
| #6 recovery and #9 OpenRouter adapter merged in PR #19; #12 harness prerequisites merged in PR #20; 33 offline tests pass. | Keep #10 open until a separately authorized human-label operation produces a text-free receipt; close this umbrella only after that outcome or an explicit block. |

## Table of contents

1. [OpenRouter lane](#openrouter-lane)
2. [Human-reference protocol lane](#human-reference-protocol-lane)

## OpenRouter lane

The verified typed Decisions API shipped with exact model and backend identity, safe key loading, mock tests, and documentation. #6's checkpointing fix remains in place. The original implementation brief is retained under this project directory as historical execution context.

QA: the offline suite passes, with no direct-TypeSafe fixture changes and no key or source text in tracked files.

## Human-reference protocol lane

The offline human-label draft under #10 exposes sampling, blinding, adjudication, minimum class support, commitment, denominators, and an advance gate. Human labeling and new model calls remain external dependencies; the draft does not claim human-reference accuracy.

QA: the protocol is self-contained, uses no raw issue text, and explicitly says that existing classification labels are a three-model consensus, not human gold. A later human operation needs its own authorization and receipt.
