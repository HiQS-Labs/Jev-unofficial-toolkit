# Jev unofficial toolkit

**The classification labels behind these results are a three-model consensus, not human gold.**

[Jev](https://docs.typesafe.ai/introduction) is TypeSafe's decision model: it evaluates state against typed questions and returns answers that software can use directly. Choice selects a label; Score returns a rubric value; both include confidence and probabilities. Noul returns a yes-probability without separate confidence. Jev is not a text generator. This independent toolkit adds provenance hashes, frozen questions and inputs, blind-label commitments, confidence gates, ordered mocks, and evaluation around the pinned `jev-1.13.0` endpoint.

**Build status:** the offline test suite and shipped fixture replays pass; CI remains mock-only. An operator-authorized [live historical-sample rerun](evidence/2026-09-20-fresh-100-live-rerun/README.md) scored purpose `89/100`, area `62/94`, and passed the original purpose gate with `72/74` correct at confidence ≥ `0.8` and coverage `74/100`. That rerun required recovery from the [probability-accessor failure](https://github.com/HiQS-Labs/Jev-unofficial-toolkit/issues/6); this version now keeps completed answers per record and scores valid choices even when an optional probability map is invalid. The historical rerun remains a repeated-sample result, not an uninterrupted CLI pass or a new unseen-sample result.

## Getting Started

**For this toolkit, get a TypeSafe API key.** Sign up or log in at the [TypeSafe console](https://console.typesafe.ai/), then obtain a key from the dashboard as described in the [official quick start](https://docs.typesafe.ai/introduction/quickstart). Store it in a private file outside the repository and pass its path with `--key-file`, or supply `TYPESAFE_API_KEY` in your environment for each live run. Never commit the key. Start with the offline examples below, then follow [Live use](#live-use-after-mock-acceptance) for the required manifest, input policy and explicit live flag.

**To explore Jev through OpenRouter**, visit [OpenRouter](https://openrouter.ai/) and choose **Sign Up**. After signing in, create an API key on the [API keys page](https://openrouter.ai/settings/keys), then consult the [OpenRouter quickstart](https://openrouter.ai/docs/quickstart) and [TypeSafe Jev listing](https://openrouter.ai/~typesafe/jev-latest) for access and usage details.

OpenRouter is a separate access route: its keys do not work with this toolkit's direct TypeSafe client, and an OpenRouter adapter has not been implemented or tested here. The linked listing follows the latest Jev version; this toolkit keeps its model pinned to `jev-1.13.0` for reproducibility.

## Use it without a key

Run from the repository root with Python 3.7 or later; the harness and tests use only the Python standard library. No SDK installation is required.

```sh
python3 -m jev replay --fixture examples/fixtures/fresh-100 --out results/fresh
python3 -m jev replay --fixture examples/fixtures/purpose-40 --out results/holdout
python3 -m jev replay --fixture examples/fixtures/ate-benchmark --out results/ate
python3 -m jev ask --state examples/ask/ate-state.json --questions ate_triage_v1 --mock-responses examples/ask/ate-mock-response.json --out results/ask
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
| `model` | Exactly `jev-1.13.0`. |
| `quiz_sha256` | SHA-256 of the exact input file bytes (`--state` or `--records`). |
| `questions_sha256` | SHA-256 of canonical question JSON; must match the frozen set. |
| `labels_sha256` | Blind annotation commitment from `guard.commit(labels_file)`; checked only after responses finish. |
| `gate` | `axis`, `confidence_floor`, `min_accuracy`, and `min_coverage`, fixed before requests. |

`guard.verify(labels_file, manifest)` verifies the commitment. Preserve the manifest in an independently committed record before annotation disclosure; a hash does not prove blindness if someone can replace both labels and manifest. `guard.verify_freeze(directory, expected)` checks file bytes against caller-pinned constants. The shipped question and fixture constants live in `guard.py`, independently of sidecars.

Metrics exclude unknown truth, use the union of declared classes and known truth as their class universe, and return zero for zero denominators. Predictions outside that universe are rejected. Confidence buckets and gates include only known-truth rows; coverage uses that same denominator. `agreement(pred, annotator_file)` requires an exact ID match and compares a JSON ID-to-label map.

## Live use, after mock acceptance

Live spend needs operator authorization. Supply `TYPESAFE_API_KEY` per run or `--key-file` pointing outside the repo; there is no key in configuration or fixtures. Live CLI calls also require `--live`, a frozen manifest, and a new output directory. For `ask`, provide `--repo`; for `eval`, every record carries its repo. The default policy allows public `HiQS-Labs` repositories only; a reviewed `--policy` JSON can configure `allowed_owners`, `denied_owners`, and `denied_repos`. Runtime visibility checks fail closed.

For historical state text, consult [Needle-fork at f7c7047](https://github.com/HiQS-Labs/Needle-fork/tree/f7c7047/TESTS-RESULTS/2026-09-19-jev-fresh-sample) outside this repository and verify the original `quiz_sha256` in the [handoff manifest](https://github.com/HiQS-Labs/Jev-unofficial-toolkit/blob/9b37264/handoff/needle-fork/TESTS-RESULTS/2026-09-19-jev-fresh-sample/manifest.json). If you transform it into this CLI's record schema, freeze the transformed file separately. Do not fetch or store issue titles or descriptions here. A separately authorized historical rerun must preserve the original receipts and be identified as a repeated-sample check, never a new unseen-sample performance claim.

The client makes at most three attempts for rate limits and server errors, honoring `Retry-After` as seconds or an HTTP date. It refuses an excessive wait, redirects, other model IDs, and other endpoints. Errors do not echo provider payloads or keys. The recursive results writer refuses `title`, `description`, `stderr`, `stdout`, and `body`; the CLI additionally projects typed fields and never writes state.

## Questions and evidence

`work_purpose_v3` preserves the original taxonomy text and question hash. Its `ci_cd`, `skills`, and `ui` glosses were script-authored, not taxonomy definitions. `ate_triage_v1` is a new implementation of the [handoff requirements](https://github.com/HiQS-Labs/Jev-unofficial-toolkit/blob/9b37264/handoff/xyz-forge/PROJECT/GH-712-JEV-ATE-TRIAGE.md#requirements); it includes the required option union, crash override, and `expects_edits` condition. Supply the structured state described there, with the specified output tails. Historical canned answers do not validate the new question wording.

Read [PROTOCOL.md](PROTOCOL.md) for the verbatim experiment rules and [USE-CASES.md](USE-CASES.md) for evidence limits and untested hypotheses. The [handoff snapshot](https://github.com/HiQS-Labs/Jev-unofficial-toolkit/tree/9b37264/handoff) remains read-only and is not a runtime dependency.

## Other OSS projects — untested potential integrations

[SemIf](https://github.com/TheoLeeCJ/SemIf) and [laya](https://github.com/NandhaKishorM/laya) are independent, non-TypeSafe OSS projects that may be candidates for future integration with this toolkit. **Neither has been tested with it.** No adapter, drop-in compatibility, or comparable accuracy is claimed; this version's client is restricted to the pinned TypeSafe model and endpoint.

## Licence

The operator selected XYZ-forge's AGPL plus commercial setup, superseding this repository's original GPL licence. See [LICENSE](LICENSE), [LICENSE-COMMERCIAL.md](LICENSE-COMMERCIAL.md), and [NOTICE](NOTICE). Needle-derived portions retain their [Apache licence](licenses/Apache-2.0.txt) and attribution. No XYZ-forge Jev implementation or TypeSafe SDK is vendored. Jev and TypeSafe are their owners' marks; this project is unofficial.
