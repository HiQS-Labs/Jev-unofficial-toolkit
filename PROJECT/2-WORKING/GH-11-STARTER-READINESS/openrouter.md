# OpenRouter phase — GH-9

> Historical phase brief. The adapter was completed in PR #19 and issue #9 is closed.

Implement #9 on the current `feat/11-starter-readiness` branch only. Read the exact issue, `GH-9-OPENROUTER-ACCESS.md`, the existing client/CLI/answers/tests and the TypeSafe/OpenRouter primary docs linked in the capture. The endpoint is the dedicated OpenRouter Decisions API, with the versioned `typesafe/jev-1.13` slug; never send a Jev decision to chat completions or the moving latest alias. Keep direct TypeSafe behavior and historical receipts stable. Use the existing stdlib patterns, text-free writer, model checks, hashes, retries and mock-only CI. The #6 checkpointing fix is already committed.

The response contract has already been verified with one operator-authorized synthetic live call; do not make another call. POST `https://openrouter.ai/api/alpha/decisions` with requested model `typesafe/jev-1.13` returned HTTP 200, concrete response model `typesafe/jev-1.13-20260917`, provider `TypeSafe`, top-level fields `answers,id,model,provider,usage`, answer fields `choice,confidence,probabilities,type`, and usage fields `cost,input_tokens,output_tokens`. The request/response SHA-256 hashes are `3a6edcb2828bf56685674c17077a68baf482e83e3e54f4f3362a79f25d1fbcfe` and `575423d147bd80c27a3ef4a754a67079e491471e9e8b06610dcbe610737d0177`. This verifies the typed contract without retaining raw state/response or key. Implement the adapter now from these facts. Never print, commit or paste the key, raw response body, source issue text or local secret path. Do not spend on a historical benchmark.

Run the focused mock suite and keep the output in the existing one-branch PR. Agy review must assess code and evidence; do not claim human approval or a performance gain.
