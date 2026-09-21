---
gh_issue: 6
source: https://github.com/HiQS-Labs/Jev-unofficial-toolkit/issues/6
title: Preserve live answers when optional probabilities fail
status: In progress
created: 2026-09-20
updated: 2026-09-20
owner: toolkit maintainer
goal: Keep valid typed answers and completed paid responses when an optional probability map or later request fails.
doc_type: bugfix
effort: 2
complexity: 2
risk: 2
phases: 1
---

# GH-6 — probability and checkpoint recovery

## Status

| What was just completed | What's next |
|---|---|
| Commit `3cf45d0` keeps each completed answer and marks invalid optional probabilities. | Run preflight and hosted CI; review before closing the issue. |

The observed historical rerun lost the first batch's in-memory answers after an optional probability validation error. The cause of the rejected distribution is not established because the failing probability map was not retained.

## Acceptance

- [ ] The typed probability accessor still rejects invalid distributions; no values are fabricated or silently normalized.
- [ ] Choice/confidence scoring remains available when only optional probabilities fail.
- [ ] Completed answers are written through the results denylist before the next request, with hashes and no state text.
- [ ] A later failed response leaves earlier checkpoints and no completed `results.json`.
- [ ] The existing fixture replays and mock-only CI pass. No new live run is needed for this fix.

## Swarm Preflight Contract

```json
{
  "target": {"repo": ".", "ref": "main"},
  "gate": "python3 -m unittest discover -s tests -q",
  "fix_probes": [{"type": "grep_absent", "path": "jev/cli.py", "pattern": "probabilities_status"}],
  "artifacts": ["jev/cli.py", "tests/test_jev_harness.py", "README.md"],
  "remediation": {"source": "self#acceptance", "criteria": "All acceptance bullets above"},
  "lanes": {"agy_safe": [], "orchestrator_only": ["jev/cli.py", "tests/test_jev_harness.py", "README.md"]}
}
```
