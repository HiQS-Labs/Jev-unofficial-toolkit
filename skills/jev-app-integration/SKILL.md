---
name: jev-app-integration
description: Build a small, tested Jev decision function inside an existing app. Use when a developer asks an agent to integrate Jev for a specific app behavior, especially when they need help turning the idea into working code. Do not use for evaluating this toolkit's historical fixtures.
---

# Build a Jev function for an app

Help the developer leave with a working function in **their app**, a focused offline test, and instructions they can follow. Explain choices in plain language, but fit the code to the app's existing language, architecture, and test setup.

## Find the decision

1. Inspect the app's relevant entry point, data flow, dependencies, and tests. Ask for the app or the missing decision only when it cannot be inferred. Identify one bounded judgment Jev should make, the state it needs, the typed answer, and the deterministic code that will use that answer. If ordinary rules fully decide it, implement those rules without a Jev call.
2. Choose `choice` for a finite label, `score` for a rubric value, or `noul` for a yes probability. Write the question criteria and an example state from the app's domain. Treat model output as decision input; keep actions, permission checks, and fallback behavior in app code. Specify what happens on low confidence, malformed responses, and transport failure. Noul has no separate confidence accessor.
3. Check the outbound-data boundary **before** constructing a live client or sending state. Define which fields and destinations the app owner permits, reduce state to those fields, and make disallowed input take a deterministic refusal or fallback path. If that policy is unknown, ask before enabling live calls. Do not assume this toolkit's CLI visibility checks protect direct client use. Never put API keys, raw state, or provider responses in committed examples or logs.

## Implement and prove it

- Use the smallest app-native function at the existing call site. For a Python app using this repo, `jev.client.JevClient.ask(state, questions)` is the **direct TypeSafe** transport. It accepts only the pinned `jev-1.13.0` model and endpoint. Read the current [client](../../jev/client.py), [answer accessors](../../jev/answers.py), and [protocol](../../PROTOCOL.md) before coding. Inject the client or a narrow callable so tests can use `MockClient` without a network request. If the app is in another language, verify the current provider contract before writing its HTTP adapter; do not present this Python client as a cross-language SDK.
- Reuse a shipped frozen question set only when its meaning fits. A custom question can be sent through `JevClient`, but the CLI loads only registered frozen sets and its evaluation path currently scores Choice only. Give custom questions an explicit version and committed hash, and define app-specific labeled examples and a measurable acceptance gate before claiming they work reliably. Do not borrow this repo's classification accuracy for a new task. Do not claim OpenRouter support through `JevClient`.
- Add a focused offline test with a realistic canned response and a negative control. Verify the intended typed result and deterministic action, the low-confidence or failure fallback where relevant, and that disallowed state never reaches the client. Run the test and report its result. `MockClient` proves wiring and policy behavior, not model quality; any live call or spend needs the app owner's explicit authorization and a suitable data policy.
- Show the developer the function and where it is called, the state and answer shapes, how to run the test, how to supply the key outside source control when live use is authorized, and which model-behavior claims still need labeled validation. Prefer one runnable path over a menu of speculative integrations.
