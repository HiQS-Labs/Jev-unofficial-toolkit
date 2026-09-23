# GH-26 commitment-anchor consult

Verdict: proceed with the additive anchored verifier; leave the historical
helpers, freeze, commitment, results, provenance and verification unchanged.

## Ground truth

The current verifier accepted a synthetic bundle in which predictions, metrics,
the response commitment and provenance were coherently replaced. The public
pre-label commitment was introduced alone at full commit
`11e84b1da82250f12bed54927230209236f50cdc` and hashes to
`bb149ea4a58101e48e6492fab3cfc6f1f0dccd9601ec24c69a00716b8b7f6d2b`.
The rerun freeze binds the original helper and scorer bytes, so those files must
not be edited post-run.

## Reconciliation

Both independent advisors agreed that Git history already preserves the
historical timeline claim and that changing frozen files would weaken the
evidence. They disagreed on whether executable hardening was necessary: one
considered direct Git inspection sufficient; the other recommended a small
attempt-specific wrapper because the verifier API still accepted coherent
substitution.

The latter view governs. The wrapper closes the reproduced automation boundary,
uses a non-configurable anchor, delegates every existing semantic check to the
frozen scorer, and makes no new claim about label blindness or arbitrary
filesystem history. Required controls are a coherent-substitution rejection and
a canonical published-artifact positive path.
