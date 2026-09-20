# Research brief: TypeSafe.ai Jev for HiQS classification and test-triage work

You are Agy, acting as an independent research advisor. Produce a written report; do not change code. Read-only on the repos. Do not call the TypeSafe API yourself; the operator holds the key. Cite every claim with a URL or a file path.

## Context you must read first

1. TypeSafe docs index: https://docs.typesafe.ai/llms.txt — read at minimum: introduction, concepts/system-one, concepts/state, primitives (choice, score, noul, advanced), confidence, patterns (fan-out, confidence-routing, composite-scoring), models, api, model-jaggedness/jev-1.13, and the cookbooks for classification_using_confidence, hierarchical_classification, consistency_choice_cookbook, autoresearch_feature_discovery, llm_guardrails.
2. XYZ-forge umbrella issue (this recon): https://github.com/HiQS-Labs/XYZ-forge/issues/709.
3. Needle-fork #31 (calibrated ModernBERT result: purpose 23/40, TF-IDF 20/40, area 10/38 vs 12/38) and Needle-fork #29 (eight-purpose taxonomy, `uncertain` / `needs_context` contract).
4. XYZ-forge #299 (Gen 4 ATE: Tier-1 $0 classifier with a 0% false-negative floor, fuzz engine, repro synthesis), `skills/ate/SKILL.md`, `utils/ate/scripts/run_variations.py` (`CLASSIFY_PROMPT`), `utils/py/calibrate_tier1.py`, `utils/py/telemetry_schema.py`.
5. Data policy: only public HiQS-Labs repo content may be sent to the API. Previous-org RebalanceOS/XYZ history, BinoidCBD and LTVera are private and off-limits.

## Questions to answer

### A. Fit and limits
1. Which of our classification targets are genuinely "System One" tasks by TypeSafe's own definition, and which are not? Be specific about work-purpose, component area, ATE pass/fail, severity, category, root-cause clustering, drift detection, and next-action prediction. For each, name the failure mode from the jaggedness page that is most likely to bite.
2. How should the `state` be structured for (a) an issue/PR title + truncated description + repo name, and (b) an ATE row (command, exit code, edit_applied flag, stdout/stderr tails)? JSON object vs string; what to filter out; where the 32k state budget matters.
3. Confidence: how is it computed and what does the docs' own guidance say about thresholds? Can it substitute for the #29 contract's `needs_context` / `uncertain` outputs, or do we still need a code-side rule?

### B. Experimental design critique
4. Lane A (40-record holdout rerun): is a zero-shot score on an already-observed holdout a fair comparison against ModernBERT/TF-IDF, given no tuning is allowed on it? What would make it unfair, and what should the protocol forbid? Propose the exact scoring table and the minimum result that would justify a follow-up (with the caveat that n=40 cannot support a promotion claim).
5. Lane B (ATE shadow): the Tier-1 classifier is held to FN = 0 on 24 known-fail rows. Is the same floor sensible for a probabilistic classifier, and at what probability threshold? Suggest how to report Jev-vs-Gemma agreement on the 143-row GH-141 log honestly given it is all failures.
6. Are there better datasets in these repos than the ones named for Lane B? (Look for any retained stderr text, `error_log.jsonl` files, or benchmark JSONL.) Note that Gen 4 telemetry stores `stderr_digest`, not text.

### C. Other experiments worth proposing
7. Rank Lanes C–F in the umbrella by expected value per hour of operator time, and add up to three experiments of your own that are (i) System One-shaped, (ii) use only public data, (iii) have an existing baseline in these repos. Candidates to consider, accept, or reject: the autoresearch cookbook pattern (Jev probabilities as features for a CatBoost/logistic head on the #31 data), hierarchical area classification with a beam over Choice probabilities, guardrails-style screening of agent transcripts for prompt injection before they enter training corpora, and a Noul-based "is this issue still valid / already fixed" check for the `/10days` sweep.
8. For each accepted experiment: baseline, dataset, question shapes (Choice/Score/Noul with draft criteria), gate, and a token/cost estimate at $0.042/Mtok.

### D. Operational
9. Pinning and drift: how should we record `model`, `usage`, and request hashes so a result stays reproducible after `jev-latest` moves?
10. Rate limits are "dynamic"; what retry policy does the Python SDK apply and what should a batch runner do at 429?
11. Anything in the TypeSafe legal/terms pages that affects sending public GitHub issue text or storing responses in a public repo.

## Output format

Markdown report, sections A–D in order, each question answered with a verdict line first, then evidence with citations. End with a one-page "recommended next three experiments" table (name, baseline, dataset, gate, cost). Flag anything you could not verify.
