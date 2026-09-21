# FAQ: Jev, Needle, and Practical AI Model Use

This FAQ collects the questions that come up when evaluating Jev and Needle for this toolkit's work. Vendor facts reflect public documentation reviewed on 2026-09-20; toolkit status reflects merged PRs #19 and #20. Jev's internal architecture and parameter count are not publicly disclosed. For what this toolkit has actually measured, read [USE-CASES.md](USE-CASES.md).

---

## 1. What is the new Jev model, and how is it similar to and different from an LLM?

**Jev** is TypeSafe AI's first "System One" model: a hosted AI decision model intended to turn unstructured application state into **typed, probabilistic decisions**. Instead of producing prose, code, or a token stream, it answers constrained questions such as:

- Which category applies?
- Is this statement true or false?
- Where does this situation lie on a defined scale?

Its documented primitives are:

- **Choice** — selects one label from developer-defined criteria; returns the choice, a probability distribution, and a confidence.
- **Score** — places the state on a developer-defined ordered scale; returns a float score, probabilities over the levels, and a confidence.
- **Noul** — returns the probability that a yes/no statement is true, with no separate confidence.

This toolkit pins `jev-1.13.0` and freezes question sets by hash; see [README.md](README.md) for the request and response contract it enforces.

### Similarities to LLMs

- Both are trained AI models that learn statistical/semantic patterns from data.
- Both can take natural-language or structured context as input.
- Both can generalize to inputs they did not see verbatim during training.
- Both can be used inside agentic or automated software workflows.

### Differences from a typical LLM

| Dimension | Jev | Typical LLM |
|---|---|---|
| Main job | Typed choices, scores, and binary judgments | Language understanding and generation |
| Output | Predeclared typed value plus probabilities | Generated text/tokens, sometimes constrained JSON |
| Generation | No autoregressive text decoding | Usually autoregressive next-token decoding |
| Best tasks | Routing, classification, scoring, gating, triage | Chat, code, writing, explanation, open-ended reasoning |
| Schema safety | Cannot emit an output outside the declared answer space | May emit invalid/malformed/unexpected output unless constrained |
| Confidence | Probability distribution is a first-class result | Confidence often requires additional design/evaluation |

Jev is best viewed as a semantic decision component, not a chatbot replacement. It is useful when software must repeatedly make a narrow decision quickly and reliably enough to feed into ordinary program logic.

---

## 2. Is Jev "artificial intelligence" or just a model? Does it have attention like GPT?

Jev is both **AI** and a **model**. "Artificial intelligence" is the broad category; a model is a trained mathematical component used by an AI system.

```text
Artificial intelligence
└── Machine learning
    └── Neural-network models
        ├── Generative language models / LLMs
        └── Specialized decision models
            └── Jev
```

Jev is an AI model because it learns patterns from data and makes probabilistic decisions for new inputs. A complete system can combine Jev with databases, rules, observability, tools, dashboards, and human escalation.

### What attention means in GPT

In GPT-style Transformers, self-attention lets tokens assign different relevance weights to other tokens in context. GPT uses **causal** self-attention: while generating a new token, it can attend to earlier tokens but not future output tokens. It generates one token at a time.

### Does Jev have GPT-style attention?

The responsible answer is: **the public documentation does not reveal enough implementation detail to confirm its exact internal attention architecture.** TypeSafe has publicly described the product as a new architecture using its RLCD training method and parallel typed-decision inference ([launch post](https://typesafe.ai/blog/introducing-system-one-models-and-jev)), but has not published weights, parameter count, a technical architecture paper, or an implementation specification.

It is plausible that Jev uses neural attention or transformer-like components—many non-generative models do—but that should not be stated as confirmed. Jev does not use GPT's autoregressive next-token-generation loop for its published decision interface.

"Attention" in machine learning is a mathematical weighting mechanism. Neither GPT nor Jev has human attention, awareness, consciousness, or intent.

---

## 3. Does Jev have a neural network?

**Yes, Jev is a neural-network-based AI model.** A model that turns input state into learned scores/probabilities over choices is a neural model, and TypeSafe describes Jev as a new model architecture trained with RLCD ("Reinforcement Learning for Calibrated Decisions"). It is not a hand-written if/then rules engine.

At a high level, a Jev request works like this:

```text
State (text, JSON, logs, application facts)
        ↓
Learned neural representation / scoring computation
        ↓
Scores for developer-defined choices or scale points
        ↓
Probability distribution and typed decision
```

For a Choice primitive, the model evaluates the supplied state against the allowed criteria and returns a probability distribution across those options; the documented contract is that the distribution sums to one. How those probabilities are computed internally is not disclosed.

### Important caveat

TypeSafe has not publicly disclosed the details needed to characterize the network precisely. Its public materials confirm the product behavior—typed primitives, parallel decision evaluation, and non-autoregressive output—but do not disclose:

- Parameter count.
- Number of layers.
- Exact neural architecture.
- Whether it is a standard Transformer, encoder-only model, hybrid, or another design.
- Exact attention mechanism, if any.
- Training data, weights, or model card.

So the defensible statement is:

> Jev has a learned neural network, but its detailed architecture is proprietary and publicly undisclosed.

It differs from GPT-style LLMs primarily in its output behavior: it does not expose a general token-generation decoder that writes arbitrary prose or code. Instead, it produces probabilities and typed answers over developer-defined output spaces in a parallel decision-oriented inference flow.

---

## 4. Would Jev likely have billions of parameters?

**It might, but the parameter count is unknown.** TypeSafe has not publicly released Jev's parameter count, model weights, training-data details, detailed architecture, or self-hosted model package.

A model designed for bounded routing/classification/scoring can be useful at sizes far below a frontier generative LLM. Jev could plausibly be sub-billion, in the 1B–10B range, or larger—but public latency and cost claims do not establish which.

| Size class | Parameter range | Plausibility |
|---|---:|---|
| Small | Under 1B | Plausible |
| Mid-sized | 1B–10B | Plausible |
| Large | 10B–70B+ | Possible, but less obviously aligned with its low-cost/low-latency positioning |
| Frontier-scale | Hundreds of billions+ | Unverified and less likely from the public product framing |

Fast service can result from a small model, but also from quantization, batching, optimized serving, specialized hardware, caching, or an architecture unlike standard LLM inference. Parameter count is therefore not proof of capability.

For a real use case, measure decision quality, confidence calibration, latency, cost, stability under noisy/missing inputs, and operational value—not just parameter count.

---

## 5. Is Needle a competitor to Jev? In which use cases?

**In some use cases, yes.** Cactus Compute's Needle is an open, on-device automation model family; Jev is a hosted decision API. They overlap wherever software needs a bounded, structured judgment from a small taxonomy: routing, enum classification, gating, extraction of a fixed schema. They diverge on where the model runs, how confidence is produced, and what the output primitive is.

### What Needle is

| Dimension | Needle 2 | Needle 3 |
|---|---:|---:|
| Model capacity | 45M parameters | Approximately 29M-121M, depending on deployed depth ([Cactus](https://cactuscompute.com/needle)) |
| File size | 14 MB | 8-29 MB |
| Context | Around 256-token sliding window | Up to 8K tokens |
| Depth | Fixed | One weight set usable at 2-20 layers |
| Architecture | Earlier compact Needle architecture | "Laddered Simple Attention Network" |
| Focus | Tool calling, device use, structured extraction | Same automation core, expanded flexible deployment |
| Languages | Earlier release positioned mainly around English | Broader multilingual positioning |

Needle 3's "intelligence laddering" means a single model artifact can run at different depths: shallower variants trade quality for lower latency and footprint; deeper variants use more of the same trained network.

Needle is still, broadly, an LLM: it accepts language-like input and emits token sequences, typically tool calls, arguments, or structured records. It is a very small, specialized, generative action model, not a general assistant; "automation foundation model" is the more useful label.

### Where Needle can compete with Jev

| Use case | Why Needle can win | What Jev offers instead |
|---|---|---|
| Data that must not leave the device or network | Runs locally; no API, no egress, no per-call cost | Hosted only; every state is sent to TypeSafe |
| Offline, edge, or constrained hardware (phones, wearables, microcontrollers) | 8-29 MB, 2-bit, runs in tens of MB of RAM | Requires network round-trip; 70-500 ms reported latency |
| Very high call volume at near-zero marginal cost | No metering once deployed | Metered per request (cheap, but nonzero) |
| Structured extraction of several fields from one input | Generative output can fill a whole record in one pass | One typed answer per declared question; free-form fields are out of scope |
| Local tool/function calling | Its native task | Not a tool caller; it selects among declared options |
| Narrow taxonomies you can fine-tune for | Open weights, fine-tuning supported | No fine-tuning; you shape behaviour through question wording |

### Where Needle does not compete

| Requirement | Jev | Needle |
|---|---|---|
| Calibrated probability distribution as a first-class output | Documented contract for Choice and Score; Noul is itself a probability | A generated label; any confidence must be derived and calibrated on your own holdout |
| Output guaranteed inside the declared answer space | By construction; no text decoding | Constrained decoding helps, but the model still generates tokens and can drift |
| Many independent questions over one state in one call | Parallel evaluation; adding questions barely changes latency | One generation per prompt; multiple questions mean multiple passes or a composite schema |
| No model hosting, serving, or quantization work | Managed API | You own deployment, updates, and depth selection |
| Semantic judgment over long or messy state | Hosted capacity | 45M-121M parameters is small; capacity is the first thing to test |

### Needle versus Jev at a glance

| | Needle 3 | Jev |
|---|---|---|
| Output | Generated tool calls / records | Typed choice, score, or binary probability |
| Autoregressive generation | Yes, as a generative automation model | No text-generation interface |
| Deployment | Open/local on constrained hardware | Proprietary hosted API |
| Best role | Local function calling, extraction, on-device bounded classification | Routing, scoring, classification, gating with calibrated probabilities |

The honest framing: Needle competes on **where** the decision runs and **what it costs**; Jev competes on **how trustworthy the probability is** and **how little serving work you take on**. A team that needs a bounded decision on private, offline, or high-volume data should evaluate both.

---

## 6. Would Needle 3 beat Jev as a classifier? How would you find out?

**Only a head-to-head measurement can say.** Needle 2 did not perform well in this toolkit's parent work (a six-action coding-core pilot in [Needle-fork](https://github.com/HiQS-Labs/Needle-fork)); the critical limitations were probably the 256-token context limit and the mismatch between a tiny tool-calling model and a planning-like task. Needle 3 is a credible rerun candidate, tracked in [Needle-fork #66](https://github.com/HiQS-Labs/Needle-fork/issues/66), because it can run at a higher-capacity 121M configuration, accept up to 8K tokens of context, produce constrained classification output, and be fine-tuned. An architecture update cannot solve poor labels, ambiguous classes, insufficient input state, or a task that requires substantial reasoning.

### The bar Jev has already set

This toolkit's recorded Jev evidence on the work-purpose taxonomy is purpose `88/100` (macro-F1 `0.687`) and, at confidence >= `0.8`, `73/75` correct with `75/100` coverage ([USE-CASES.md](USE-CASES.md)). A Needle 3 challenger on the same frozen sample and labels would need to match that accuracy *and* supply a confidence signal that gates as cleanly; without the second half it is a classifier, not a substitute.

### Why Needle 3 could close the gap

- More capacity at deeper settings: up to about 121M parameters.
- Longer context: task, plan, recent tool trace, test failure, and compact repository state can be supplied together.
- Structured enum classification, with a confidence you calibrate yourself.
- Fine-tuning support for a narrow taxonomy, which Jev does not offer.
- Embeddings that enable a separate retrieval/classifier comparison.

### Why it might still lose

- Choosing the next coding action can require interpreting tests, diffs, code semantics, architectural constraints, and incomplete evidence.
- A 44-label taxonomy can contain genuine ambiguity: several reasonable next actions may exist.
- Valid enum output does not mean correct semantic classification.
- Model confidence must be calibrated on your own held-out dataset; Jev's is a documented contract.

### Recommended head-to-head

Use the same session-grouped temporal holdout, the same frozen question wording, and the same blind labels for every candidate, with the gate pre-registered before the sample is drawn (the rules in [PROTOCOL.md](PROTOCOL.md)). Compare:

- Majority, repeat-last, and Markov baselines.
- TF-IDF plus logistic regression or LightGBM.
- Embeddings plus nearest-neighbor or linear classifier.
- Fine-tuned ModernBERT-base classifier.
- Needle 2.
- Needle 3 at 8, 12, and 20 layers.
- Optional fine-tuned Needle 3.
- Jev, pinned, through this toolkit.
- A frontier coding model as an upper-bound reference.

Measure macro-F1, per-class precision/recall, top-3 accuracy, confusion matrices, selective accuracy at confidence thresholds, coverage, calibration, latency, memory, and cost per decision.

A useful production pattern is confidence-gated routing, whichever model wins:

```text
High-confidence result -> offer/perform low-risk suggestion
Low confidence or complex state -> retrieval, stronger local model, frontier model, or human
```

For the existing 44-label next-action problem, Needle 3 is a hypothesis to evaluate against Jev, not a safe standalone planner.

---

## 7. What are three practical skill-file ideas that use Jev?

The most useful Jev skills are those in which Jev makes a narrow semantic judgment and deterministic code retains control of execution. All three below are tracked as issues [#13](https://github.com/HiQS-Labs/Jev-unofficial-toolkit/issues/13), [#14](https://github.com/HiQS-Labs/Jev-unofficial-toolkit/issues/14), and [#15](https://github.com/HiQS-Labs/Jev-unofficial-toolkit/issues/15). The shared harness prerequisites in closed issue [#12](https://github.com/HiQS-Labs/Jev-unofficial-toolkit/issues/12) now support frozen Choice/Score/Noul bundles, offline scoring, deterministic policy composition, and typed decision logs. The three designs still have no live outcome evidence; each needs its own baseline and pre-registered gate per [USE-CASES.md](USE-CASES.md).

### Skill 1: `jev-agent-action-gate`

**Purpose:** Evaluate proposed agent actions before risky, expensive, irreversible, or scope-sensitive operations.

**Example input:**

```json
{
  "agent": "codex",
  "repo": "store-monitor",
  "branch": "feature/checkout-retries",
  "task": "Fix duplicate charges after a checkout retry timeout",
  "operation": {
    "type": "shell_command",
    "command": "git push origin main --force"
  },
  "changed_files": [
    ".github/workflows/deploy.yml",
    "src/payments/retry.ts"
  ],
  "tests_status": "not_run"
}
```

**Questions:**

- Choice: `allow`, `confirm`, or `block`.
- Score: local/reversible through destructive/production-sensitive risk.
- Noul: "The operation is appropriately scoped to the stated task."
- Noul: "The operation touches sensitive or production-affecting systems."

**Policy:** Deterministic deny/allow rules always take precedence. Jev can trigger confirmation or flag semantic scope creep; it must not be the final authorization system.

**Why it is useful:** It fits agent hooks, centralized prompt/activity logs, audit trails, and shadow-mode deployment.

### Skill 2: `jev-next-step-router`

**Purpose:** Route an agent state to the appropriate decision source instead of trying to make Jev itself a full coding planner.

**Possible workflow modes:**

```text
inspect
implement
validate
document_or_commit
clarify_or_escalate
```

**Possible routing targets:**

```text
deterministic
retrieval
local_predictor
frontier_model
human
```

**Questions:**

- Choice: which workflow mode applies?
- Choice: which decision source should handle the next step?
- Score: how sufficient is the available evidence?
- Noul: does the current candidate set include a safe appropriate action?
- Noul: does this decision need deeper code/debugging/architectural reasoning?

**Why it is useful:** It turns the difficult "predict the one correct next action" problem into bounded judgments about ambiguity, evidence sufficiency, and escalation. It can govern when to trust local predictors, retrieval, or a stronger model.

### Skill 3: `jev-commerce-incident-triage`

**Purpose:** Turn quantitative e-commerce anomaly signals into a stable incident category and deterministic escalation decision.

**Upstream data:**

- Order anomaly probability and observed-versus-expected order rate.
- Sessions, add-to-cart events, checkout starts, payment outcomes.
- Synthetic product/cart/checkout test results.
- Payment failure and HTTP error rates.
- Inventory state, campaign changes, and recent deployment metadata.

**Incident categories:**

```text
normal_variation
traffic_or_marketing_change
inventory_or_catalog_issue
checkout_or_site_incident
payment_or_fraud_incident
needs_investigation
```

**Questions:**

- Choice: incident category.
- Score: severity from informational to critical.
- Noul: is there direct functional/technical failure evidence?
- Noul: should the system escalate now?

**Policy:** Page/create an incident only when deterministic statistical and technical criteria agree with the Jev result—for example, a sustained extreme order anomaly, normal traffic, and a synthetic checkout failure or sharply increased payment failures.

**Why it is useful:** It makes the semantic classification of a complex multi-signal event consistent, while leaving numerical baselines, threshold checks, and side effects in ordinary code.

### Shared skill contract

Use a common observable pattern for all Jev skills:

```text
Normalize state
→ Apply deterministic preconditions
→ Ask Jev a bundle of independent primitives
→ Compose answers with deterministic policy
→ Act / request review / escalate
→ Write immutable decision log
→ Store eventual outcome label
```

A useful log record includes skill/version, model/version, schema version, normalized input fingerprint, answers, probabilities, confidence, deterministic rule hits, final decision, human override, observed outcome, and latency.

Use pinned model versions for evaluation and production. Evaluate a newer *pinned* version in shadow mode before changing behavior; this toolkit refuses the `jev-latest` alias by design ([PROTOCOL.md](PROTOCOL.md) rule 1), so a shadow run is a second exact version string, never the alias.

---

## 8. What are six practical applications for Jev?

**Support routing.** Classify an incoming request by topic, urgency, and destination team, then route only high-confidence results automatically. Send ambiguous or sensitive cases to a person.

**CI failure triage.** Turn exit codes, test summaries, and approved log fields into a bounded failure category and severity score. Let deterministic code select the runbook or escalation channel.

**Agent action review.** Judge whether a proposed tool action matches the stated task, appears unusually risky, or needs confirmation. Keep permissions, denylists, and execution authority in ordinary code.

**Document intake.** Sort contracts, applications, or operational forms into a fixed workflow and flag records that appear incomplete. Use field validation and human review for final acceptance decisions.

**Data quality monitoring.** Classify anomalous records by likely cause, such as missing fields, format drift, duplication, or upstream feed failure. Combine the result with measured thresholds before opening an incident.

**Trust and safety queues.** Prioritize reports into a predefined review taxonomy and estimate whether immediate escalation is warranted. Never use the model as the sole basis for punitive, legal, or safety-critical action.

---

## Practical takeaway

- Use **Jev** as a fast semantic decision layer: classify, route, score, gate, and triage.
- Use ordinary statistics, deterministic code, and explicit thresholds for numeric truth, authorization, safety, and side effects.
- Use stronger LLMs where you need code understanding, long-form explanations, broad reasoning, synthesis, or generation.
- Treat **Needle 3** as a possible Jev competitor for on-device, offline, private, or high-volume bounded classification; decide by head-to-head measurement on the same frozen sample, not by assumption, and never treat it as a planner.
- Measure every deployed decision system using task-specific accuracy, calibration, abstention/coverage, latency, cost, false positives, and ultimately operational outcome.
