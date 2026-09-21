---
gh_issue: 9
source: https://github.com/HiQS-Labs/Jev-unofficial-toolkit/issues/9
title: Add pinned OpenRouter Jev access
status: In progress
created: 2026-09-20
updated: 2026-09-20
owner: toolkit maintainer
goal: Support the versioned Jev decision API through OpenRouter if its typed contract can be verified.
doc_type: feature
effort: 3
complexity: 4
risk: 2
phases: 2
---

# GH-9 — OpenRouter access

## Status

| What was just completed | What's next |
|---|---|
| OpenRouter lists `typesafe/jev-1.13`; `~typesafe/jev-latest` moves. | Verify the decisions API request/response contract and implement a small isolated transport only if it preserves typed answers. |

## Table of contents

1. [Discovery](#discovery)
2. [Mock implementation](#mock-implementation)
3. [Swarm Preflight Contract](#swarm-preflight-contract)

## Acceptance

- [ ] Document the exact supported OpenRouter model slug, endpoint, authentication variable/key-file mechanism, and any response-shape differences from TypeSafe's System One API. If a pinned Jev slug is unavailable or typed responses cannot be preserved, record that constraint and keep support explicitly unsupported rather than silently route through the moving alias.
- [ ] Use canonical requests and SHA-256 request/response provenance, bounded retries, model identity checks, usage accounting, and the current text-free results policy at the same level as the direct path. Keep backend identity explicit in results so direct TypeSafe and OpenRouter scores cannot be pooled accidentally.
- [ ] Mock-only green/red controls cover an OpenRouter response, wrong model, malformed response, no key, and routing isolation. CI makes no live requests. Any live verification or spend is a separate operator-authorized step.
- [ ] README explains both access routes without implying that an OpenRouter key works with the direct client. Update the issue #1 evidence boundary if any new benchmark is run.

Current starter status: direct TypeSafe path has live evidence; OpenRouter compatibility has not been tested.

## Discovery

OpenRouter's [versioned model listing](https://openrouter.ai/typesafe/jev-1.13) establishes a stable slug. Its [Jev lab](https://openrouter.ai/labs/jev/compile) shows `openRouter.alpha.decisions.create` with `model: 'typesafe/jev-1.13'`, `state` and `questions`. Primary OpenRouter material confirms the dedicated `POST https://openrouter.ai/api/alpha/decisions` route: the [Jev lab](https://openrouter.ai/labs/jev/compile) sends `state` and typed `questions` through `alpha.decisions.create`, and the [OpenRouterTeam provider changelog](https://github.com/OpenRouterTeam/ai-sdk-provider/blob/main/CHANGELOG.md) names that route. The versioned slug is `typesafe/jev-1.13`, distinct from the moving `~typesafe/jev-latest` alias. Auth is an OpenRouter bearer key. A bounded synthetic response still needs to confirm exact returned model, usage fields and probability shape before the implementation is declared compatible. The generic chat-completions route is not the Jev Decisions API.

QA: If typed decision transport cannot be verified, document the constraint in #9 and leave OpenRouter unsupported. Do not ship a guessed adapter.

## Mock implementation

Keep direct TypeSafe requests unchanged. Use only standard library code. An OpenRouter key remains separate from `TYPESAFE_API_KEY`, and the result identifies backend and model so reports cannot mix the two. Reuse canonical hashes, retry bounds, result filtering, and mock behavior. Add green/red mock controls and update README with the verified use path. No CI network calls.

QA: Run the offline suite and both mock paths. A live OpenRouter smoke test, if run, uses synthetic text and a new output directory; it never reruns historical data or publishes key bytes.

## Swarm Preflight Contract

```json
{
  "target": {"repo": ".", "ref": "main"},
  "gate": "python3 -m unittest discover -s tests -q",
  "fix_probes": [{"type": "path_absent", "path": "jev/openrouter.py"}],
  "artifacts": ["jev/openrouter.py", "jev/cli.py", "tests/test_jev_harness.py", "README.md"],
  "artifacts_new": ["jev/openrouter.py"],
  "remediation": {"source": "self#discovery", "criteria": "Verify typed transport before adapter; then satisfy Mock implementation QA"},
  "lanes": {"agy_safe": [], "orchestrator_only": ["jev/openrouter.py", "jev/cli.py", "tests/test_jev_harness.py", "README.md"]}
}
```
