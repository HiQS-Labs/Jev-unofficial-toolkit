# Jev unofficial toolkit

[Project site](https://hiqs-labs.github.io/Jev-unofficial-toolkit/) · [GitHub repository](https://github.com/HiQS-Labs/Jev-unofficial-toolkit) · [XYZ Forge flagship project](https://github.com/HiQS-Labs/XYZ-forge)

**The classification labels behind these results are a three-model consensus, not human gold.**

[Jev](https://docs.typesafe.ai/introduction) is TypeSafe's decision model: it evaluates state against typed questions and returns answers that software can use directly. Choice selects a label; Score returns a rubric value; both include confidence and probabilities. Noul returns a yes-probability without separate confidence. Jev is not a text generator. This independent toolkit adds provenance hashes, frozen questions and inputs, blind-label commitments, confidence gates, ordered mocks, and evaluation around the pinned `jev-1.13.0` endpoint.

**Build status:** the offline test suite and shipped fixture replays pass; CI remains mock-only. An operator-authorized [live historical-sample rerun](evidence/2026-09-20-fresh-100-live-rerun/README.md) scored purpose `89/100`, area `62/94`, and passed the original purpose gate with `72/74` correct at confidence ≥ `0.8` and coverage `74/100`. That rerun required recovery from the [probability-accessor failure](https://github.com/HiQS-Labs/Jev-unofficial-toolkit/issues/6); this version now keeps completed answers per record and scores valid choices even when an optional probability map is invalid. The historical rerun remains a repeated-sample result, not an uninterrupted CLI pass or a new unseen-sample result.

## Getting Started

**For this toolkit, get a TypeSafe API key.** Sign up or log in at the [TypeSafe console](https://console.typesafe.ai/), then obtain a key from the dashboard as described in the [official quick start](https://docs.typesafe.ai/introduction/quickstart). Store it in a private file outside the repository and pass its path with `--key-file`, or supply `TYPESAFE_API_KEY` in your environment for each live run. Never commit the key. Start with the offline examples below, then follow [Live use](#live-use-after-mock-acceptance) for the required manifest, input policy and explicit live flag.

**To explore Jev through OpenRouter**, visit [OpenRouter](https://openrouter.ai/) and choose **Sign Up**. After signing in, create an API key on the [API keys page](https://openrouter.ai/settings/keys), then consult the [OpenRouter quickstart](https://openrouter.ai/docs/quickstart) and the [versioned TypeSafe Jev listing](https://openrouter.ai/typesafe/jev-1.13) for access and usage details.

OpenRouter is a separate access route: use `--backend openrouter` with `OPENROUTER_API_KEY` or `--key-file` containing an OpenRouter key. The default `--backend typesafe` uses `TYPESAFE_API_KEY` or a TypeSafe key file; keys are never borrowed from the other backend.

The adapter sends canonical `state`, `questions`, and `model` JSON to **`POST https://openrouter.ai/api/alpha/decisions`**, requesting **`typesafe/jev-1.13`** with bearer authentication. It never uses chat completions or the moving latest alias. The [provider changelog](https://github.com/OpenRouterTeam/ai-sdk-provider/blob/main/CHANGELOG.md) documents the dedicated Decisions route.

An operator-authorized synthetic contract check returned the concrete model `typesafe/jev-1.13-20260917` and provider `TypeSafe`; the adapter accepts exactly that response identity and fails closed on other revisions. The typed `answers` retain Choice, Score, and Noul accessors. OpenRouter additionally returns `id`, `provider`, and usage fields `input_tokens`, `output_tokens`, and `cost`; the adapter validates and totals all three usage fields without retaining arbitrary response extensions. The live check established the Choice response contract, not Score/Noul live behavior or benchmark accuracy. No additional live call or historical benchmark was run for this implementation.

For an authorized live request, use the same frozen-input and repository-policy requirements as the direct route:

```sh
python3 -m jev ask --backend openrouter --state STATE.json --questions work_purpose_v3 --repo HiQS-Labs/REPO --manifest MANIFEST.json --live --out results/openrouter-new
```

Supply `OPENROUTER_API_KEY` in the environment or add `--key-file FILE`. The manifest must specify `"backend": "openrouter"` and `"model": "typesafe/jev-1.13"`, plus the hashes below. For offline use, replace `--live` with `--mock-responses FILE` containing an ordered list of Decisions response objects with the concrete response model, provider, and usage fields above. New results and per-record checkpoints explicitly identify their backend; OpenRouter reports also include provider, output tokens and cost. The shipped historical fixtures remain TypeSafe-only and their receipt results remain unchanged.

## Use it without a key

Run from the repository root with Python 3.7 or later; the harness and tests use only the Python standard library. No SDK installation is required.

```sh
python3 -m jev replay --fixture examples/fixtures/fresh-100 --out results/fresh
python3 -m jev replay --fixture examples/fixtures/purpose-40 --out results/holdout
python3 -m jev replay --fixture examples/fixtures/ate-benchmark --out results/ate
python3 -m jev ask --state examples/ask/ate-state.json --questions ate_triage_v1 --mock-responses examples/ask/ate-mock-response.json --out results/ask
python3 -m jev ask --state examples/ask/gate-state.json --questions agent_action_gate_v1 --mock-responses examples/ask/gate-mock-response.json --out results/gate
python3 -m unittest discover -s tests -v
```

The `ask` line shows the structured ATE state shape (`command`, `exit_code`, `signal`, `expects_edits`, `edit_applied`, `stdout_tail`, `stderr_tail`) on a synthetic run that exits `0` with a crash signature in `stderr_tail`. Its mock response is illustrative, not a recorded Jev answer; `results/ask/answers.json` receives typed choices and hashes only, never the state.

Each output directory must be new. Tests block Python networking and external process execution, while transport tests use canned HTTP responses. The live client also refuses requests when `CI` is set. Nothing runs a live experiment in CI.

The reproduced receipt metrics and their limits are:

| Fixture | Expected result from the handoff | What replay can establish |
| --- | --- | --- |
| [Fresh sample](https://github.com/HiQS-Labs/Jev-unofficial-toolkit/blob/9b37264/handoff/needle-fork/TESTS-RESULTS/2026-09-19-jev-fresh-sample/jev/results.json) | Purpose `88/100`; macro-F1 `0.6868054177836787`; at confidence ≥ `0.8`, `73/75` correct and coverage `75/100` | Recompute from consensus labels and retained choices/confidences, including both axes and annotator agreement. Historical metadata is carried unchanged for a byte-comparison against the original results. |
| [Older holdout](https://github.com/HiQS-Labs/Jev-unofficial-toolkit/blob/9b37264/handoff/needle-fork/TESTS-RESULTS/2026-09-18-jev-purpose-zero-shot/results.json) | Purpose `37/40`; area `32/38` | Recompute metrics from stored confusion matrices. Ordered prediction replay is separate; unpublished per-ID truth and confidence-bucket correctness are not reconstructed. |
| [ATE benchmark](https://github.com/HiQS-Labs/Jev-unofficial-toolkit/blob/9b37264/handoff/xyz-forge/TESTS-RESULTS/2026-09-18+GH-712/benchmark/summary.json) | FN `1`, FP `0`; historical `fn_zero_threshold` `0.48` | Recompute argmax confusion, FN/FP, and Tier-1 agreement. The threshold is retained as a cited historical value, not an independent recomputation: the rows have no `P(fail)`. The fixture manifest's gate requires perfect `status` accuracy at floor `0.0`, so replay prints `met=False`; the historical zero-FN floor is reported separately as `fn_floor_met` under `benchmark`. |

The API response bytes, per-record token usage, and probability distributions were not retained. Mocks contain only recorded typed choices and confidence, with no invented probabilities. `answers.json` hashes the reconstructed requests/responses; `replay.json` separately identifies the historical hashes. Copied run dates, token totals, script hashes, and visibility in reconstructed historical results describe the original experiment, not this mock run.

`fn_zero_threshold(truth, fail_probabilities)` computes the minimum actual `P(fail)` among known failures, using `P(fail) >= threshold`. It refuses a sample without failures. This is an in-sample statistic, not evidence of a future zero-FN guarantee. The ATE fixture reports `fn_zero_threshold: null` alongside `recorded_fn_zero_threshold: 0.48` to preserve the evidence boundary.

## CLI and input contract

`python3 -m jev` is the single CLI, with `ask`, `eval`, and `replay` commands. Use `--mock-responses FILE` for an ordered JSON list of response objects. Missing answers, unsupported choices, exhausted mocks, unused mocks, duplicate IDs, empty records, and missing models are errors. Scoring does not require probabilities.

Each completed response is also saved as `answer-0001.json`, `answer-0002.json`, and so on before the next request. If a later request fails, these text-free checkpoints remain in the reserved output directory; `answers.json` and `results.json` appear only after the batch completes. An invalid optional probability map is omitted and marked `probabilities_status: "invalid"`; the typed probability accessor still rejects it, and no probabilities are normalized or invented.

- `ask --state FILE --questions NAME --out DIR` reads a JSON state value and returns typed answers. For a mock, supply an ordered response list containing only that request's response.
- `eval --records FILE --labels FILE --questions NAME --manifest FILE --out DIR` evaluates a JSON list of `{id, repo, state}` records. Labels are a JSON list of `{id, purpose, area}` or the chosen question IDs. Use `null` for unknown truth. Add `--mock-responses FILE` for offline work.
- `replay --mock-responses FILE --records FILE --labels FILE --manifest FILE --out DIR` uses the same evaluation path without network access. `--fixture DIR` selects the shipped, hash-pinned evidence fixtures instead.

A manifest contains:

| Field | Contract |
| --- | --- |
| `backend` | `typesafe` (default when absent), or `openrouter` explicitly. Must match `--backend`. |
| `model` | `jev-1.13.0` for TypeSafe; `typesafe/jev-1.13` for OpenRouter. |
| `quiz_sha256` | SHA-256 of the exact input file bytes (`--state` or `--records`). |
| `questions_sha256` | SHA-256 of canonical question JSON; must match the frozen set. |
| `labels_sha256` | Blind annotation commitment from `guard.commit(labels_file)`; checked only after responses finish. |
| `gate` | `axis`, `confidence_floor`, `min_accuracy`, and `min_coverage`, fixed before requests. |
| `scored_axes` | Optional nonempty list of unique frozen question IDs. The gate axis must be included. |
| `score_tolerance` | Required when a scored axis uses Score; a nonnegative rubric-level tolerance. |
| `noul_threshold` | Required when a scored axis uses Noul; a threshold in `[0, 1]`. |

`guard.verify(labels_file, manifest)` verifies the commitment. Preserve the manifest in an independently committed record before annotation disclosure; a hash does not prove blindness if someone can replace both labels and manifest. `guard.verify_freeze(directory, expected)` checks file bytes against caller-pinned constants. The shipped question and fixture constants live in `guard.py`, independently of sidecars.

Metrics exclude unknown truth, use the union of declared classes and known truth as their class universe, and return zero for zero denominators. Predictions outside that universe are rejected. Confidence buckets and gates include only known-truth rows; coverage uses that same denominator. `agreement(pred, annotator_file)` requires an exact ID match and compares a JSON ID-to-label map.

## Live use, after mock acceptance

Live spend needs operator authorization. Supply `TYPESAFE_API_KEY` per run or `--key-file` pointing outside the repo; there is no key in configuration or fixtures. Live CLI calls also require `--live`, a frozen manifest, and a new output directory. For `ask`, provide `--repo`; for `eval`, every record carries its repo. The default policy allows public `HiQS-Labs` repositories only; a reviewed `--policy` JSON can configure `allowed_owners`, `denied_owners`, and `denied_repos`. Runtime visibility checks fail closed.

For historical state text, consult [Needle-fork at f7c7047](https://github.com/HiQS-Labs/Needle-fork/tree/f7c7047/TESTS-RESULTS/2026-09-19-jev-fresh-sample) outside this repository and verify the original `quiz_sha256` in the [handoff manifest](https://github.com/HiQS-Labs/Jev-unofficial-toolkit/blob/9b37264/handoff/needle-fork/TESTS-RESULTS/2026-09-19-jev-fresh-sample/manifest.json). If you transform it into this CLI's record schema, freeze the transformed file separately. Do not fetch or store issue titles or descriptions here. A separately authorized historical rerun must preserve the original receipts and be identified as a repeated-sample check, never a new unseen-sample performance claim.

The client makes at most three attempts for rate limits and server errors, honoring `Retry-After` as seconds or an HTTP date. It refuses an excessive wait, redirects, other model IDs, and other endpoints. Errors do not echo provider payloads or keys. The recursive results writer refuses source-text fields including `state`, `title`, `description`, `stderr`, `stdout`, `body`, `command`, `task`, `summary`, `diff_summary`, `text`, `content`, and `prompt`; the CLI additionally projects typed fields and never writes state.

## Questions and evidence

`work_purpose_v3` preserves the original taxonomy text and question hash. Its `ci_cd`, `skills`, and `ui` glosses were script-authored, not taxonomy definitions. `ate_triage_v1` is a new implementation of the [handoff requirements](https://github.com/HiQS-Labs/Jev-unofficial-toolkit/blob/9b37264/handoff/xyz-forge/PROJECT/GH-712-JEV-ATE-TRIAGE.md#requirements); it includes the required option union, crash override, and `expects_edits` condition. Supply the structured state described there, with the specified output tails. Historical canned answers do not validate the new question wording.

Read [PROTOCOL.md](PROTOCOL.md) for the verbatim experiment rules and [USE-CASES.md](USE-CASES.md) for evidence limits and untested hypotheses. [FAQ.md](FAQ.md) answers background questions about Jev, Needle, and where each fits; it is orientation, not evidence. The [handoff snapshot](https://github.com/HiQS-Labs/Jev-unofficial-toolkit/tree/9b37264/handoff) remains read-only and is not a runtime dependency.

## Bounded-judgment skills

Three skill designs are tracked as issues [#13](https://github.com/HiQS-Labs/Jev-unofficial-toolkit/issues/13) (agent action gate), [#14](https://github.com/HiQS-Labs/Jev-unofficial-toolkit/issues/14) (next-step router), and [#15](https://github.com/HiQS-Labs/Jev-unofficial-toolkit/issues/15) (commerce incident triage). The shared harness prerequisites in [#12](https://github.com/HiQS-Labs/Jev-unofficial-toolkit/issues/12) are implemented: schema validation, Score/Noul scoring, typed decision logs, exact model overrides, and deterministic policy composition. **None of the three skill designs has live outcome evidence yet.** Each needs its own frozen question set, blind labels, and pre-registered gate before its first live request; nothing inherits the classification results above. The `gate` example line above runs the frozen `agent_action_gate_v1` question set offline with illustrative mock answers. Its hook, shadow deployment, and live thresholds remain work under #13.

The harness supports all three primitives under the [provider contract](https://docs.typesafe.ai/primitives):

| Type | Question fields | Answer fields | Label in `--labels` | Metrics |
| --- | --- | --- | --- | --- |
| `choice` | `instructions`, `criteria` `{label: gloss}` (both nonempty) | `choice`, `confidence`, optional `probabilities` | label string | accuracy, macro-F1, confusion, confidence buckets, gate |
| `score` | `instructions`, `criteria` ordered list of ≥ 2 level descriptions | `score` float in `[0, N−1]`, `confidence`, optional `probabilities` | number (rubric level) | correct within `score_tolerance`, MAE, confidence buckets, gate |
| `noul` | `instructions` only | `noul` probability | `true` / `false` | correct at `noul_threshold`, Brier |

`null` marks unknown truth for any type. A manifest that scores a Score axis must carry `score_tolerance` (≥ 0) and one that scores a Noul axis must carry `noul_threshold` (in `[0, 1]`); a missing key is refused before any request, like a missing gate. Noul has no confidence, so it cannot be the gate axis. Invalid question shapes are refused before the first request.

`jev.policy.decide(policy, answers, rule_hits)` composes a decision deterministically: an ordered list of clauses, each `any`/`all` over leaf conditions (`{"rule": name}`, or `{"axis": a, "choice": c | "min": x | "max": x | "min_confidence": f}`); the first clause that holds wins and no match returns the policy's `default`, which callers set to the fail-closed value. The policy is plain JSON, so `policy_sha256` can be frozen and logged. `jev.guard.decision_record(...)` builds one decision-log row from an `Answer` (typed answers, confidence, probabilities, request/response hashes, rule hits, decision, override, outcome, latency) and `append_decision(path, record)` appends it as one JSON line; the recursive denylist applies, so the log can never carry state.

The text boundary is the caller's: the toolkit sends state to Jev and never writes it, but a hook must hash or redact free text (`task`, `command`, `diff_summary`, …) before anything is logged. `guard.DENIED` now also refuses `state`, `command`, `task`, `summary`, `diff_summary`, `text`, `content`, and `prompt` as a backstop; the guarantee remains the typed projection.

`JEV_MODEL=jev-<major>.<minor>.<patch>` overrides the pinned model for a shadow run against a manifest that names that exact version; aliases such as `jev-latest` are refused at import, with an uncaught `ValueError: model must be an exact pinned version`. The shipped fixtures pin `jev-1.13.0` and refuse under an override — that is the freeze working.

To add a frozen question set: write `jev/questions/<name>.json` (canonical JSON, keys sorted), write its SHA-256 to `jev/questions/<name>.sha256`, and add the same hash to `FROZEN_QUESTIONS` in `guard.py`. `load_questions` refuses anything else.

### Adapted from jbt95/jev-toolkit

Four pieces are ported from the MIT-licensed [jbt95/jev-toolkit](https://github.com/jbt95/jev-toolkit) (attribution in [NOTICE](NOTICE)). **None has labeled validation here; borrowed wording starts at zero evidence.**

- `--repeat N` (1–10) sends each record N identical times and writes a per-record `drift` report (distinct choices, modal share, value and confidence ranges); only the first answer is scored.
- `--redact` masks credential assignments and Bearer tokens, replaces fenced code with `[code]`, and clips long strings in state before sending. It is opt-in so historical request hashes stay reproducible.
- `failure_triage_v1` is a frozen set (failure class, blocks work, safe to suppress). `jev.loops.LoopGuard` counts failure fingerprints and escalates once at three sightings in 24 hours; `identity_request` asks whether a reworded failure is one already counted.
- `jev.routing.route_request` / `route` pick one skill from a caller-owned catalog and route only above confidence and dependence floors — a starting point for #14.

Routing and identity questions are built per call, so they cannot be frozen; failure text and tasks always travel in state, never in question wording.

## Other OSS projects — bounded evidence and untested potential integrations

[SemIf](https://github.com/TheoLeeCJ/SemIf) and [laya](https://github.com/NandhaKishorM/laya) are independent, non-TypeSafe OSS projects. A pinned SemIf/Qwen3.5-4B direct-MLX arm scored [`24/100` on the same six-action holdout](evidence/2026-09-22-semif-six-action/README.md) used in issue #21: above Jev's recorded `21/100` original result but below the `26/100` majority baseline. The serializers and readouts differ, so this is not a byte-identical request comparison, adapter validation, or drop-in compatibility claim. Laya remains untested. This version's runtime integrations still support only the pinned TypeSafe and OpenRouter Decisions routes described above.

## Build a Jev function in your app

The [Jev app integration skill](skills/jev-app-integration/SKILL.md) helps a coding agent inspect your app, add one function for a specific Jev decision, and test it with an offline mock. Ask your agent: “Use `jev-app-integration` to add a function that [describe the decision] in [app path].” Bring a sample input and the action you want for each answer. The agent should give you the changed function, a focused test, and run instructions. New question wording and new app behavior still need their own labeled validation before you rely on model quality; live requests require your authorization. For the broader multi-agent engineering system behind this work, visit [XYZ Forge](https://github.com/HiQS-Labs/XYZ-forge).

## Licence

The operator selected [XYZ Forge](https://github.com/HiQS-Labs/XYZ-forge)'s AGPL plus commercial setup, superseding this repository's original GPL licence. See [LICENSE](LICENSE), [LICENSE-COMMERCIAL.md](LICENSE-COMMERCIAL.md), and [NOTICE](NOTICE). Needle-derived portions retain their [Apache licence](licenses/Apache-2.0.txt) and attribution. No XYZ Forge Jev implementation or TypeSafe SDK is vendored. Jev and TypeSafe are their owners' marks; this project is unofficial.
