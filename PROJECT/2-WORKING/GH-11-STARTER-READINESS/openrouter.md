# OpenRouter phase — GH-9

Implement #9 on the current `feat/11-starter-readiness` branch only. Read the exact issue, `GH-9-OPENROUTER-ACCESS.md`, the existing client/CLI/answers/tests and the TypeSafe/OpenRouter primary docs linked in the capture. The endpoint is the dedicated OpenRouter Decisions API, with the versioned `typesafe/jev-1.13` slug; never send a Jev decision to chat completions or the moving latest alias. Keep direct TypeSafe behavior and historical receipts stable. Use the existing stdlib patterns, text-free writer, model checks, hashes, retries and mock-only CI. The #6 checkpointing fix is already committed.

Before implementation, verify the response contract with a single synthetic live call if needed; the operator supplied an OpenRouter key path outside this repo. Never print, commit or paste the key, raw response body, source issue text or local secret path. Store only typed/hashes and generic contract facts. Do not spend on a historical benchmark. If the typed response cannot be verified, document the blocker and stop this lane rather than guessing.

Run the focused mock suite and keep the output in the existing one-branch PR. Agy review must assess code and evidence; do not claim human approval or a performance gain.
