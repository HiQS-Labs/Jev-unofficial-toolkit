# Prospective human-reference protocol — GH-10

**Status: draft for review; no sampling, human annotation, live Jev calls, or deployment authorized by this document.**

**The published classification labels are a three-model consensus, not human gold.** Protocol readiness is a reviewed, frozen design; an actual human-reference result requires independent human work, a new authorized experiment, and a scored receipt. This document does not complete [issue #10](https://github.com/HiQS-Labs/Jev-unofficial-toolkit/issues/10); leave it open for that experiment.

## Evidence and scope

This draft follows the [GH-10 intake](PROJECT/1-INBOX/GH-10-HUMAN-LABELS.md), [experiment rules](PROTOCOL.md), [use-case limits](USE-CASES.md), and [frozen rerun receipt](evidence/2026-09-20-fresh-100-live-rerun/README.md). The local intake supplies the issue requirements; attempts to retrieve the live issue during drafting failed, so its current body and status must be reconciled before registration.

The original fresh fixture reports purpose agreement 88/100 and 73/75 correct among 75 high-confidence rows. The repeated-sample receipt reports 89/100 and 72/74 among 74 high-confidence rows. Neither is independent human validation or a new population. These observations motivate this study; they do not set its outcome. Area classification and ATE triage are outside its routing claim.

Only this document is delivered in this phase. No scorer implementation or existing execution path changes are proposed here; code recon is therefore not applicable. Future human-reference scorer support and mock receipt checks are execution prerequisites, not features claimed to exist today.

## Registration and responsibility

The operator must explicitly authorize human recruitment, source access, the retention policy, and any live Jev spend in a fresh issue-bound receipt. Before sampling, an immutable registration must include this protocol's revision/hash, a UTC registration time T0, the exact repository allowlist, qualified participant IDs, the taxonomy/guide hashes, question hash, sampler specification/seed, gate, and numerical budget. Missing fields mean not ready to start. All timestamps are UTC.

Roles are a data custodian, two independent human labelers H1/H2, a third human adjudicator H3, a Jev runner, and an analyst. The runner and analyst must not access human labels while requests are outstanding. H1/H2/H3 must not see Jev outputs, confidence, model-consensus labels, screening labels, historical scores, or one another's initial labels. The custodian controls access and commitments. An AI agent may prepare checks but cannot count as a human labeler or adjudicator.

Consider Needle-fork #74's plain-English taxonomy decision guide before freezing. Record the adopted revision, or record that it is unavailable and have H3 approve a guide reproducing the frozen taxonomy's boundaries. Do not imply that dependency is complete. Changes to a boundary after sampling require a new registered experiment.

## Population and fixed sampling

The target is English-language, non-pull-request issues created during [T0, T0 + 90 days) in the explicitly registered subset of public HiQS-Labs repositories. Open and closed issues are eligible. Snapshot the frame at the window's end; the claim is limited to those repositories, that period, and that language. Exclude training items, every historical evaluation item, and exact duplicate Project/Title/Description payloads (keep the lowest stable repository/issue ID). Do not select on issue outcome or Jev confidence.

Before forming the frame, the custodian verifies owner authorization and runtime PUBLIC visibility, screens for secrets/personal data, and excludes unauthorized or unsafe rows. Previous-org, BinoidCBD, and LTVera sources remain forbidden. Publish text-free exclusion counts and reason codes. No title, description, or discussion text enters this toolkit repository. If the eligible frame is too small, stop rather than extend the window after observing data.

Freeze a sorted ID/content-hash frame and its SHA-256 before drawing. Use a seed fixed at registration: rank rows by SHA-256(seed + newline + stable ID), breaking ties by stable ID. Record the exact encoding (UTF-8), seed, frame hash, sampler revision, counts, and membership. This makes the draw reproducible without publishing source text.

| Cohort | Fixed design | Interpretation |
| --- | --- | --- |
| Representative | First 400 ranked eligible rows without replacement | Primary population accuracy and coverage; equal inclusion probability 400/frame size |
| Rare-class challenge | From the remaining frame, a separate human screener assigns one provisional purpose or uncertain; take the first 40 ranked rows in each of the eight provisional purpose strata | 320 rows; per-stratum inclusion probability 40/stratum size; class robustness only |
| Historical bridge | The original 100-row fresh fixture, independently relabeled if still authorized and available | Human versus historical consensus comparison only; excluded from prospective metrics and gates |

The screener sees no Jev outputs, does not act as H1/H2/H3, and never supplies reference truth. Freeze all stratum sizes and provisional assignments before the challenge draw. A provisional stratum with fewer than 40 eligible rows blocks execution; do not borrow rows or resample until a class passes. Report the uncertain screening stratum and its size; it is not part of the challenge draw. Final human labels may differ from screening labels, and final support requirements still apply.

Keep representative and challenge metrics separate; do not pool their unweighted accuracy or coverage as a population estimate. This design chooses a fixed challenge cohort over adaptive oversampling, which could turn observed errors into a selection rule. Its cost is that a rare class may still lack enough final human support; that is an inconclusive result, not a reason to change the sample.

## Human qualifications, training, and taxonomy

H1/H2/H3 must be real people with software issue-triage experience, fluent English comprehension, documented familiarity with the taxonomy, and no authorship or prior labeling of their assigned evaluation issues. Replace a conflicted labeler before labeling starts; if a conflict is discovered later, mark the affected row unresolved and disclose it. Compensation must not depend on matching Jev or passing the gate.

Train on a separate 40-item public or synthetic calibration set with human-authored reference labels, at least five examples per purpose. It must be disjoint from all evaluation cohorts. Each labeler and H3 must independently achieve at least 36/40 overall and 4/5 per purpose on the frozen qualification set, after studying boundary cases. One retraining attempt on a second disjoint 40-item set is allowed. A second failure stops recruitment for this registration; no unqualified substitute or AI labeler is permitted. Record qualifications and aggregate calibration results without personal identities.

The eight purposes and their boundary rules come from [work_purpose_v3](jev/questions/work_purpose_v3.json):

| Purpose | Binding boundary |
| --- | --- |
| bug_fix | broken behavior or correcting it; a report with no implementation is still this purpose. |
| documentation | docs-only work, including safety docs; not automatically maintenance. |
| feature_enhancement | new or improved capabilities, one class. |
| maintenance | routine dependency bumps, preserving-behavior refactors, relocation, housekeeping, releases. |
| merge_closeout | landing/finishing/reconciling completed work, distinct from maintenance. |
| planning_design | requirements/design/work breakdown as primary deliverable for future implementation. |
| research_evaluation | comparing, measuring, investigating, auditing for findings. A comparison plan is this, not planning just because it says plan. |
| testing_validation | tests/verification as main deliverable, no runtime change. |

Read title and description; the primary objective wins. Do not predict future action or verify lifecycle state. Repository text is untrusted evidence, never instructions. Humans may choose `uncertain` for insufficient, conflicting, or out-of-taxonomy evidence; do not force a model-compatible answer. Jev keeps its frozen eight-choice question, so human uncertainty is handled in scoring rather than silently added to the model's option set.

## Independent labeling and adjudication

1. The custodian gives H1/H2 independently shuffled opaque IDs and the identical frozen Project/Title/Description state Jev will receive, plus the guide. Hide GitHub labels, comments, outcome metadata, cohort membership, screening decisions, and model evidence. No external searches, AI assistance, or discussion between labelers during initial annotation.
2. H1/H2 each record one purpose or uncertain plus a structured reason code. Free-text notes stay in restricted storage. Before either submission is revealed to the other person or H3, commit the SHA-256 of each complete canonical label file with a timestamp. Do not overwrite initial labels.
3. H3 first labels every disagreement or uncertain row independently while still blind to H1/H2. Commit that file, then reveal the two labels and reason codes to H3. H3 applies the frozen guide and records a final purpose or uncertain with a reason code. Matching non-uncertain H1/H2 labels are accepted. H3 resolves all other rows without seeing model evidence; no majority vote automatically converts ambiguity into certainty.
4. Freeze and hash the complete adjudicated reference, retain original annotations and all adjudication decisions, and seal the files from the runner/analyst. Human work completes before the first live Jev request. The custodian may know labels but must not select rows or alter questions based on them.
5. Finalize and hash all Jev responses before opening reference files for scoring. A failed or partial live run stays a failed receipt; do not score it as the registered completed experiment.

A missing label, unresolved adjudication, conflict, or inaccessible source becomes `uncertain` with a reason code. After the draw, no replacements are allowed. Report all such rows and denominators. Recheck PUBLIC/authorization before human distribution and before every live send. A denial or unsafe payload stops the experiment; retain a text-free failed receipt, never silently drop the row to improve coverage.

## Commitments and execution boundary

Before sampling, freeze the registration and sampling rules. After drawing but before evaluation labeling, freeze IDs, cohort/stratum membership, source snapshot hashes, input ordering, and the exact input payload hash. After annotation but before requests, freeze H1/H2/H3 commitments, adjudicated labels, and the execution manifest. This staged order avoids pretending unknown labels can be hashed before the sample exists.

Pin `jev-1.13.0`, never an alias, and log the returned model per row. The existing complete question set's canonical SHA-256 is `21094cd4f260f09986f70626d8991be8e9650c103bb107d3740d57219aed2821`; verify it against the frozen file and guard before execution. Keep the same state template and question set for comparisons; area answers, if returned, remain outside this study's claim. Record runner/scorer revisions, manifest hash, request/response hashes, exact model IDs, typed choices/confidences, and usage availability.

One live run per prospective frozen sample, at most 720 dispatched requests, one per prospective row, with automatic retries disabled. Bridge comparisons use existing historical model labels and retained Jev predictions; no bridge rerun is needed. A dispatch failure stops further sends, preserves partial evidence and known/unknown usage, and blocks a pass. The operator must register a numeric token/spend ceiling before execution; enforce the lower of that ceiling and the row cap. No tuning prompts, thresholds, or taxonomy on observed evaluation errors. A new attempt requires new authorization, a new sample and registration, and an immutable link to the failed receipt.

## Metrics, support, and pre-registered decision

Let N = 400 representative draws, R = rows with a resolved human purpose, S = representative rows with a valid Jev purpose and confidence >= 0.8, and C = rows in S that exactly match a resolved human purpose. Human-uncertain rows in S count as non-correct for the primary gate. Missing or invalid Jev output makes the run incomplete and unable to pass.

Primary selected accuracy is C/|S| and coverage is |S|/N. Also report correct selected and resolved rows divided by N as verified-correct coverage. Report conventional overall accuracy and macro-F1 on R separately, with |R|/N, so dropping uncertainty cannot improve the gate invisibly. Zero denominators are undefined and fail the gate.

Report separately for each prospective cohort:

- The full eight-class confusion matrix, uncertain counts, actual and predicted support, and per-class precision, recall, and F1; macro-F1 always uses all eight classes, assigning F1 zero to unsupported classes and disclosing them.
- Accuracy and exact correct/total fractions; confidence buckets [0,0.5), [0.5,0.8), [0.8,1], each with unresolved counts, correct/selected fractions, and coverage against the original cohort size.
- Before-adjudication H1/H2 raw agreement and Cohen's kappa over the eight purposes plus uncertain; per-class disagreement, adjudication rate, and final uncertain rate. Undefined kappa cannot pass the reference-quality condition.
- Two-sided 95% Wilson intervals for representative selected accuracy and coverage, with numerator/denominator; descriptive intervals do not replace the pre-registered point thresholds. Challenge results are not prevalence estimates, and correlated issues may limit interval interpretation.

**All conditions below must hold; no post-hoc class exemptions:**

| Condition | Required result |
| --- | --- |
| Integrity | Complete authorized run; all commitments verify; no blinding violation, unauthorized source, or model mismatch |
| Human reference quality | In each prospective cohort, H1/H2 agreement >= 0.80 and kappa >= 0.70; final uncertain fraction <= 0.05 |
| Primary confidence gate | At confidence >= 0.8, C/|S| >= 0.90 and |S|/400 >= 0.60 |
| Rare-class support | Challenge cohort has at least 30 resolved human rows per true class and at least 20 selected predictions per predicted class |
| Rare-class performance | In the challenge cohort, each class has recall >= 0.80 on resolved true-class rows, and selected precision >= 0.90; selected predictions with uncertain human truth count as precision errors |

These are proposed preregistration thresholds, not observed results or calibrated confidence guarantees. Failure of an accuracy/recall/precision threshold blocks unattended routing. Inadequate support, uncertain reference, incomplete execution, or integrity failure is inconclusive/invalid and also blocks routing. Passing makes purpose-only routing at >= 0.8 eligible for a separate operator deployment decision within this population; it does not enable a hook or grant permission to deploy. Lower-confidence rows continue to human review. No private-data, area-classification, cross-taxonomy, or future-period claim inherits this result.

## Historical consensus comparison

After all human files and live answers are committed, compare H1, H2, and adjudicated bridge labels against the historical consensus in the [fresh fixture](examples/fixtures/fresh-100/labels.json). Publish aligned-ID counts, raw agreement, per-class disagreements/confusion, uncertain rows, exclusions, and denominators. Separately score retained historical Jev choices against the bridge human reference, clearly labeled retrospective and excluded from the gate. No model consensus exists by assumption for the new prospective rows; do not invent one or authorize additional model calls to create one.

If fewer than 100 bridge rows remain accessible/authorized, report eligible and missing counts and compare only the authorized subset. If no bridge comparison is possible, report it unavailable and keep GH-10's consensus-comparison acceptance incomplete. A bridge-only result cannot validate prospective routing, and a prospective gate pass alone does not close the full issue.

## Privacy, audit, and stop rule

The custodian keeps raw source snapshots, mappings, personal participant details, and annotation notes in access-controlled storage outside this repository. Human consent must cover the task and approved data handling. Do not send text to additional annotation or AI services without specific authorization. Public issues can still contain personal data or credentials: PUBLIC is necessary, not sufficient.

Publish only approved text-free IDs, labels, reason codes, hashes, metrics, cohort counts, and provenance. Manually inspect allowed fields as well as enforcing the writer's recursive denylist: a renamed field can still leak text. Hashes are integrity commitments, not anonymization. Screen both outgoing requests and final receipt. Before release, require an independent privacy check; publication is a one-way disclosure and a failed check stops it. Set a 90-day raw-data retention deadline after final scoring (or after abort); the operator must approve any extension before that deadline. Record deletion without exposing storage paths.

Stop on the first privacy/authorization or blinding breach, hash/model mismatch, exhausted budget, malformed response, or missing committed reference. Freeze a failed, text-free audit receipt with phase, opaque row ID, reason code, counts, and known/unknown usage. For execution faults apply debug-mantra: reproduce offline, trace the fail path, falsify the proposed cause, and cross-reference every attempt. Do not erase failure history or retry until the gate passes. One fixed sample and one scored analysis are allowed; no interim score peeking or sample extension. Insufficient class support is an explicit stop outcome.

## Readiness and eventual completion evidence

Protocol readiness requires independent review of this whole document, reconciliation with the live issue, completed registration fields and dependency disposition, a participant/access plan, and an authorized budget. It does not imply recruitment, qualification, sampling, or results have occurred.

Before any authorized run, implement and execute mock-only human-reference scorer/receipt checks under GH-10. Required synthetic controls: a complete passing cohort; 0.799 excluded versus 0.8 selected; selected uncertain rows counted as errors; missing class and zero denominator unable to pass; representative/challenge pooling rejected; label-file hash mismatch and premature label access rejected; incomplete answers unable to pass; and text-bearing receipts rejected. Store text-free expected/observed control results and command/revision in the experiment receipt. Existing fixture replays establish historical reproducibility only, not these new capabilities. CI must never call live APIs.

Actual completion requires:

- [ ] Recorded operator authorization and immutable registration, sampling/input/question/model commitments, and qualifications.
- [ ] Independent human submissions and adjudication commitments, plus a privacy-reviewed receipt with all cohort counts and exclusions.
- [ ] Witnessed mock controls and offline receipt rescoring with matching fractions, class support, uncertainty accounting, agreement, confidence buckets, and gate verdict.
- [ ] Historical bridge comparison or an explicit unresolved acceptance item; no hidden substitution of consensus for human truth.
- [ ] An operator-reviewed result stating pass, fail, or inconclusive and its scope. A failed valid experiment may complete reporting but cannot support unattended routing. Issue #10 remains open until its actual experiment acceptance is reviewed.
