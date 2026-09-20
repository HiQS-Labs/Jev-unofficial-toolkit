Annotator answer files for GH-69. One JSONL per annotator, 100 rows, format in `../QUIZ.md`.

- `codex-astra-xh.jsonl` — Codex gpt-6-astra, extra-high reasoning; committed by the operator.
- `claude.jsonl` — Claude, labelled blind before Codex ran; added only after Codex's file is in and
  must hash to `manifest.json → commitments.claude_sha256`.
- `consensus.jsonl` — agreed rows plus operator adjudications (added later).
