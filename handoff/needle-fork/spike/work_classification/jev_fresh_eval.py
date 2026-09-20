"""Jev zero-shot on the GH-69 fresh sample, scored against the consensus labels.

Reuses jev_zero_shot.py unchanged: the same frozen QUESTIONS (criteria committed at 453cae1),
the same text template, request builder, client, metrics and confidence buckets. Adds only the
inputs (quiz.jsonl + consensus.jsonl), the visibility re-check, and the pre-registered gate:
on the purpose axis, rows with Jev confidence >= 0.8 must be >= 90% accurate and cover >= 60%
of the scored (non-uncertain) rows.

    python spike/work_classification/jev_fresh_eval.py \
        --sample TESTS-RESULTS/2026-09-19-jev-fresh-sample --key-file <secret>
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import jev_zero_shot as jz  # noqa: E402

GATE = {"axis": "purpose", "confidence_floor": 0.8, "min_accuracy": 0.90, "min_coverage": 0.60}


def gate_result(truth, pred, conf, floor=GATE["confidence_floor"]):
    scored = [i for i, t in enumerate(truth) if t is not None]
    high = [i for i in scored if conf[i] >= floor]
    hits = sum(1 for i in high if truth[i] == pred[i])
    accuracy = (hits / len(high)) if high else 0.0
    coverage = (len(high) / len(scored)) if scored else 0.0
    return {"scored_rows": len(scored), "high_confidence_rows": len(high), "high_confidence_correct": hits,
            "accuracy": accuracy, "coverage": coverage,
            "met": accuracy >= GATE["min_accuracy"] and coverage >= GATE["min_coverage"], **GATE}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", required=True, help="the frozen sample directory")
    ap.add_argument("--model", default=jz.MODEL)
    ap.add_argument("--key-file")
    a = ap.parse_args(argv)
    d = Path(a.sample)
    manifest = json.loads((d / "manifest.json").read_text())
    quiz_bytes = (d / "quiz.jsonl").read_bytes()
    if jz.sha256_bytes(quiz_bytes) != manifest["quiz_sha256"]:
        raise SystemExit("quiz.jsonl does not match manifest.json quiz_sha256")
    records = [json.loads(l) for l in quiz_bytes.decode("utf-8").splitlines() if l.strip()]
    out = d / "jev"
    if out.exists():
        raise SystemExit(f"{out} exists; one run per frozen sample")
    visibility = jz.repo_visibility(r["repo"] for r in records)
    sendable = [r for r in records if visibility.get(r["repo"]) == "PUBLIC"]
    skipped = [r["id"] for r in records if visibility.get(r["repo"]) != "PUBLIC"]
    key = jz.load_key(a)

    started = dt.datetime.now(dt.timezone.utc).isoformat()
    responses, hashes, models, tokens = [], [], set(), 0
    for rec in sendable:
        body = jz.build_request(rec, a.model)
        parsed, raw_req, raw_resp = jz.call_jev(body, key, os.environ.get("TYPESAFE_API_URL", jz.ENDPOINT))
        responses.append(parsed)
        hashes.append({"id": rec["id"], "request_sha256": jz.sha256_bytes(raw_req), "response_sha256": jz.sha256_bytes(raw_resp)})
        models.add(parsed.get("model"))
        tokens += int(parsed.get("usage", {}).get("input_tokens", 0))
    finished = dt.datetime.now(dt.timezone.utc).isoformat()

    # Labels are read only now, after every response is in.
    labels = {json.loads(l)["id"]: json.loads(l) for l in (d / "answers" / "consensus.jsonl").read_text().splitlines() if l.strip()}
    results = {"utc_started": started, "utc_finished": finished, "model_requested": a.model,
               "models_seen": sorted(m for m in models if m), "input_tokens": tokens,
               "records": len(records), "sent": len(sendable), "skipped_ids": skipped,
               "quiz_sha256": manifest["quiz_sha256"], "consensus_sha256": jz.sha256_file(d / "answers" / "consensus.jsonl"),
               "questions_sha256": jz.sha256_bytes(jz.canonical(jz.QUESTIONS)),
               "script_sha256": {"jev_zero_shot.py": jz.sha256_file(Path(jz.__file__)), "jev_fresh_eval.py": jz.sha256_file(Path(__file__))},
               "label_sources": dict(Counter(l["source"] for l in labels.values())),
               "visibility": visibility, "axes": {}, "predictions": []}
    for axis in ("purpose", "area"):
        truth = [None if labels[r["id"]][f"{axis}_primary"] == "uncertain" else labels[r["id"]][f"{axis}_primary"] for r in sendable]
        pred = [resp["answers"][axis]["choice"] for resp in responses]
        conf = [float(resp["answers"][axis].get("confidence", 0.0)) for resp in responses]
        results["axes"][axis] = {"metrics": jz.metrics(truth, pred, jz.CLASSES[axis]),
                                 "confidence_buckets": jz.confidence_table(truth, pred, conf),
                                 "prediction_counts": dict(Counter(pred))}
        if axis == GATE["axis"]:
            results["gate"] = gate_result(truth, pred, conf)
        # agreement with each annotator, for the record
        for name in ("claude", "codex-astra-xh"):
            ann = {json.loads(l)["id"]: json.loads(l) for l in (d / "answers" / f"{name}.jsonl").read_text().splitlines() if l.strip()}
            results["axes"][axis][f"agree_with_{name}"] = sum(1 for r, p in zip(sendable, pred) if ann[r["id"]][f"{axis}_primary"] == p)
    for rec, resp in zip(sendable, responses):
        results["predictions"].append({"id": rec["id"], **{
            f"{axis}_{k}": resp["answers"][axis].get(k) for axis in ("purpose", "area") for k in ("choice", "confidence")}})
    out.mkdir(parents=True)
    (out / "results.json").write_text(json.dumps(results, indent=1, sort_keys=True) + "\n")
    (out / "requests.jsonl").write_text("".join(json.dumps(h) + "\n" for h in hashes))
    for axis in ("purpose", "area"):
        m = results["axes"][axis]["metrics"]
        print(f"{axis}: {m['correct']}/{m['labeled_n']} raw_accuracy={m['raw_accuracy']:.4f} macro_f1={m['macro_f1']:.4f}", file=sys.stderr)
    g = results["gate"]
    print(f"gate ({g['axis']}, conf>={g['confidence_floor']}): accuracy {g['high_confidence_correct']}/{g['high_confidence_rows']}={g['accuracy']:.4f}, "
          f"coverage {g['high_confidence_rows']}/{g['scored_rows']}={g['coverage']:.4f} -> {'MET' if g['met'] else 'NOT MET'}", file=sys.stderr)
    print(f"model(s) {results['models_seen']}, input tokens {tokens}, wrote {out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
