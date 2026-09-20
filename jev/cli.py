"""One CLI: ask, eval, replay. Live use is explicit and never allowed in CI."""
import argparse
import json
import os
from collections import Counter
from pathlib import Path

from .answers import MODEL, number
from .client import JevClient, MockClient, canonical, load_key, sha256
from .eval import (agreement, binary_counts, confidence_table, gate, metrics,
                   metrics_from_confusion)
from .guard import (FROZEN_FIXTURES, POLICY, load_questions, repo_visibility,
                    verify, verify_freeze, write_results)


def read_json(path):
    return json.loads(Path(path).read_text())


def keyed(rows):
    if not isinstance(rows, list) or not rows or any(not isinstance(r, dict) or not isinstance(r.get("id"), str) or not r["id"] for r in rows):
        raise ValueError("nonempty records with string IDs required")
    result = {r["id"]: r for r in rows}
    if len(result) != len(rows):
        raise ValueError("duplicate IDs")
    return result


def score(rows, labels, questions, gate_config, annotators=None):
    lookup = keyed(labels)
    if set(keyed(rows)) != set(lookup):
        raise ValueError("label IDs must exactly match completed records")
    axes, predictions = {}, []
    for row in rows:
        predictions.append({"id": row["id"], **{
            f"{axis}_{field}": row["answers"][axis][field]
            for axis in questions for field in ("choice", "confidence")}})
    for axis, question in questions.items():
        if question["type"] != "choice":
            raise ValueError("evaluation supports Choice questions only")
        truth = [lookup[r["id"]][axis] for r in rows]
        pred = [r["answers"][axis]["choice"] for r in rows]
        conf = [r["answers"][axis]["confidence"] for r in rows]
        axes[axis] = {"metrics": metrics(truth, pred, question["criteria"]),
                      "confidence_buckets": confidence_table(truth, pred, conf),
                      "prediction_counts": dict(Counter(pred))}
        for name, labels_by_axis in (annotators or {}).items():
            axes[axis]["agree_with_" + name] = agreement(
                {r["id"]: p for r, p in zip(rows, pred)}, labels_by_axis[axis])["correct"]
    axis = gate_config["axis"]
    report = {"axes": axes, "predictions": predictions}
    if axis in questions:
        report["gate"] = {"axis": axis, **gate(
            [lookup[r["id"]][axis] for r in rows],
            [r["answers"][axis]["choice"] for r in rows],
            [r["answers"][axis]["confidence"] for r in rows],
            gate_config["confidence_floor"], gate_config["min_accuracy"], gate_config["min_coverage"])}
    return report


def run(args):
    fixture = Path(args.fixture) if args.fixture else None
    if fixture:
        if args.command != "replay":
            raise ValueError("fixtures are for replay only")
        verify_freeze(fixture, {k: v for k, v in FROZEN_FIXTURES[fixture.name].items()
                                if k not in ("labels.json", "annotators.json", "confusions.json", "expected.json")})
        args.records, args.labels = fixture / "records.json", fixture / "labels.json"
        args.mock_responses = fixture / "responses.json"
        args.manifest = fixture / "manifest.json"
        args.questions = read_json(args.manifest)["questions"]
    questions = load_questions(args.questions)
    manifest = read_json(args.manifest) if args.manifest else {}
    if args.command == "ask":
        records = [{"id": "ask", "repo": args.repo, "state": read_json(args.state)}]
        input_path = args.state
    else:
        records = read_json(args.records)
        input_path = args.records
    keyed(records)
    mock = args.mock_responses is not None
    if args.command == "replay" and not mock:
        raise ValueError("replay requires --mock-responses or --fixture")
    if manifest:
        if manifest["model"] != MODEL or manifest["questions_sha256"] != sha256(canonical(questions)):
            raise ValueError("manifest model/questions mismatch")
        if manifest["quiz_sha256"] != sha256(Path(input_path).read_bytes()):
            raise ValueError("input freeze mismatch")
    if not mock:
        if os.environ.get("CI"):
            raise ValueError("live requests are disabled in CI")
        key = load_key(args.key_file)
        if not args.live or not manifest:
            raise ValueError("live use requires --live and a frozen --manifest")
        client = JevClient(key)
        policy = read_json(args.policy) if args.policy else POLICY
        visibility = repo_visibility([r["repo"] for r in records], policy)
        sendable = [r for r in records if visibility[r["repo"]] == "PUBLIC"]
    else:
        client = MockClient(read_json(args.mock_responses))
        visibility, sendable = {}, records
    if not sendable:
        raise ValueError("no eligible records")
    skipped = [r["id"] for r in records if r not in sendable]
    needs_labels = args.command != "ask" and manifest.get("mode") != "confusion"
    if needs_labels:
        if not args.labels:
            raise ValueError("evaluation requires --labels")
        config = manifest.get("gate")
        if not config:
            raise ValueError("evaluation requires a pre-registered gate in --manifest")
        if config["axis"] not in questions:
            raise ValueError("gate axis not in questions")
        for field in ("confidence_floor", "min_accuracy", "min_coverage"):
            number(config[field], unit=True)
        if "labels_sha256" not in manifest:
            raise ValueError("evaluation requires a blind label commitment")
    if manifest.get("mode") in ("confusion", "benchmark") and not fixture:
        raise ValueError("receipt-specific replay requires a pinned fixture")
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=False)  # Reserve before any paid request; failures remain reserved.
    completed = []
    for record in sendable:
        answer = client.ask(record["state"], questions)
        # Project typed fields only; never persist state, arbitrary API extensions, or error text.
        values = {}
        for name, question in questions.items():
            kind = question["type"]
            values[name] = {"type": kind, kind: getattr(answer, kind)(name)}
            if kind in ("choice", "score"):
                values[name]["confidence"] = answer.confidence(name)
                if "probabilities" in answer.response["answers"][name]:
                    values[name]["probabilities"] = answer.probabilities(name)
        completed.append({"id": record["id"], "model": answer.model, "answers": values,
                          "request_sha256": answer.request_sha256, "response_sha256": answer.response_sha256})
    if mock:
        client.finish()
    write_results(out / "answers.json", completed)
    report = {"model_requested": MODEL, "models_seen": sorted(client.models_seen),
              "input_tokens": client.input_tokens, "records": len(records), "sent": len(completed),
              "skipped_ids": skipped, "visibility": visibility, "questions_sha256": sha256(canonical(questions))}
    if fixture:
        # Recheck all fixture bytes only after responses are finalized, including labels.
        verify_freeze(fixture, FROZEN_FIXTURES[fixture.name])
        write_results(out / "replay.json", {
            "mode": "reconstructed_mock_scoring", "mock_input_tokens": client.input_tokens,
            "historical_hashes": read_json(fixture / "historical-hashes.json"),
            "fixture_sha256": FROZEN_FIXTURES[fixture.name],
            "original_response_bytes_available": False})
    if manifest.get("mode") == "confusion":
        if not fixture:
            raise ValueError("confusion replay requires a pinned fixture")
        matrices = read_json(fixture / "confusions.json")
        report = read_json(fixture / "metadata.json")
        report["axes"] = {axis: {"metrics": metrics_from_confusion(
            data["confusion"], data["confusion_labels"], data["uncertain_truth_n"])}
            for axis, data in matrices.items()}
        report["predictions"] = [{"id": r["id"], **{
            f"{axis}_{field}": r["answers"][axis][field]
            for axis in questions for field in ("choice", "confidence")}} for r in completed]
    elif needs_labels:
        # First access to label content: all answers are now finalized on disk.
        verify(args.labels, manifest)
        labels = read_json(args.labels)
        if set(keyed(labels)) != set(keyed(records)):
            raise ValueError("label IDs must match the entire input including skipped rows")
        labels = [r for r in labels if r["id"] not in skipped]
        annotators = read_json(fixture / "annotators.json") if fixture and (fixture / "annotators.json").exists() else None
        scored_questions = {k: v for k, v in questions.items() if k in manifest.get("scored_axes", questions)}
        computed = score(completed, labels, scored_questions, config, annotators)
        if fixture and manifest.get("mode") == "classification":
            report = read_json(fixture / "metadata.json")
        report.update(computed)
        if manifest.get("mode") == "benchmark":
            lookup = keyed(labels)
            truth = [lookup[r["id"]]["status"] for r in completed]
            pred = [r["answers"]["status"]["choice"] for r in completed]
            report["benchmark"] = binary_counts(truth, pred)
            tier1 = read_json(fixture / "reference.json")["tier1"]
            report["benchmark"]["tier1_agreement"] = {
                "agree": sum(p == tier1[r["id"]] for r, p in zip(completed, pred)),
                "anomaly": sum(v == "anomaly" for v in tier1.values())}
            report["benchmark"].update({"fn_zero_threshold": None,
                "recorded_fn_zero_threshold": manifest["recorded_fn_zero_threshold"],
                "threshold_provenance": manifest["threshold_provenance"]})
    write_results(out / "results.json", report)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(prog="jev")
    parser.add_argument("command", choices=("ask", "eval", "replay"))
    for name in ("state", "records", "labels", "mock-responses", "manifest", "fixture", "key-file", "policy", "repo"):
        parser.add_argument("--" + name)
    parser.add_argument("--questions", default="work_purpose_v3")
    parser.add_argument("--out", required=True)
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args(argv)
    try:
        report = run(args)
    except (ValueError, KeyError, TypeError, OSError, RuntimeError):
        # Exceptions can contain arbitrary input or provider content. Do not echo them.
        parser.exit(2, "jev: input, policy, transport, or output contract refused; no raw data logged\n")
    for name, axis in report.get("axes", {}).items():
        m = axis["metrics"]
        print(f"{name}: {m['correct']}/{m['labeled_n']}")
    if "gate" in report:
        g = report["gate"]
        print(f"gate: {g['high_confidence_correct']}/{g['high_confidence_rows']}; coverage {g['high_confidence_rows']}/{g['scored_rows']}; met={g['met']}")
    return 0
