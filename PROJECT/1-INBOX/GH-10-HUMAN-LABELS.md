---
gh_issue: 10
source: https://github.com/HiQS-Labs/Jev-unofficial-toolkit/issues/10
title: Validate purpose classification against human labels
status: Proposed (1-INBOX — not yet active)
created: 2026-09-20
updated: 2026-09-20
owner: toolkit maintainer
goal: Establish a prospective human reference and a pre-registered gate before unattended routing.
doc_type: feedback
effort: 5
complexity: 5
risk: 4
phases: 2
---

# GH-10 — human-label validation

The historical work-purpose labels are a three-model consensus, not human gold. Agreement among models does not prove correctness. This issue requires a newly sampled, independent human reference before a deployment claim.

## Acceptance

- [ ] Before any sampling or Jev request, specify the target population, sample/stratification (including rare classes), human labeler qualifications, independent blind labeling/adjudication procedure, minimum per-class support, primary metrics, and a pre-registered confidence gate. Explicitly define what result would allow or block unattended routing.
- [ ] Freeze the inputs, taxonomy, question set, model, sampling manifest, human-label commitment and gate. Keep raw issue titles/descriptions outside this toolkit repo; commit only text-free IDs, labels, predictions, hashes, aggregates and allowed provenance. Ensure no private or unauthorized repository data is sent or published.
- [ ] Report agreement among human labelers and against the historical model-consensus labels. Score Jev against adjudicated human labels, including errors by class, confidence buckets and coverage. State any uncertain or excluded rows and denominators. No extrapolation from the old 100-row sample.
- [ ] Add mock-only scorer/receipt checks; no live API calls in CI. Live Jev spend or new human labeling operation requires explicit operator authorization and a fresh issue-bound receipt.

Potential dependency: Needle-fork #74 (plain-English taxonomy decision guide) should be considered before the protocol is frozen. Existing labeling caveats are already documented; this issue requests evidence, not a wording-only correction.

## Swarm Preflight Contract

```json
{
  "target": {"repo": ".", "ref": "main"},
  "gate": "python3 -m unittest discover -s tests -q",
  "fix_probes": [{"type": "path_absent", "path": "HUMAN-LABEL-PROTOCOL.md"}],
  "artifacts": ["HUMAN-LABEL-PROTOCOL.md"],
  "artifacts_new": ["HUMAN-LABEL-PROTOCOL.md"],
  "remediation": {"source": "self#intake-and-acceptance", "criteria": "Prepare offline protocol; do not claim human-reference completion without human annotation"},
  "lanes": {"agy_safe": ["HUMAN-LABEL-PROTOCOL.md"], "orchestrator_only": []}
}
```
