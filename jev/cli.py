"""One CLI: ask, eval, replay. Live use is explicit and never allowed in CI."""
import argparse
import json
import os
from collections import Counter
from pathlib import Path

from .answers import MODEL, number
from .client import JevClient, MockClient, canonical, load_key, request_bytes, sha256
from .eval import (agreement, binary_counts, confidence_table, gate, hit_equal, metrics,
                   metrics_from_confusion, noul_metrics, score_metrics, within)
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


def scoring_parameters(manifest, questions):
    """Pre-registered scoring parameters: required whenever an axis of that type is scored, never defaulted."""
    kinds = {question["type"] for question in questions.values()}
    scoring = {}
    if "score" in kinds:
        if "score_tolerance" not in manifest:
            raise ValueError("a scored Score axis requires score_tolerance in --manifest")
        scoring["score_tolerance"] = number(manifest["score_tolerance"])
        if scoring["score_tolerance"] < 0:
            raise ValueError("score_tolerance must be nonnegative")
    if "noul" in kinds:
        if "noul_threshold" not in manifest:
            raise ValueError("a scored Noul axis requires noul_threshold in --manifest")
        scoring["noul_threshold"] = number(manifest["noul_threshold"], unit=True)
    return scoring


def score(rows, labels, questions, gate_config, annotators=None, scoring=None):
    lookup = keyed(labels)
    if set(keyed(rows)) != set(lookup):
        raise ValueError("label IDs must exactly match completed records")
    scoring = scoring or {}
    axes, predictions = {}, []
    for row in rows:
        entry = {"id": row["id"]}
        for axis in questions:
            answer = row["answers"][axis]
            entry[f"{axis}_{answer['type']}"] = answer[answer["type"]]
            if "confidence" in answer:
                entry[f"{axis}_confidence"] = answer["confidence"]
        predictions.append(entry)
    hits = {}
    for axis, question in questions.items():
        kind = question["type"]
        truth = [lookup[r["id"]][axis] for r in rows]
        pred = [r["answers"][axis][kind] for r in rows]
        if kind == "noul":
            axes[axis] = {"metrics": noul_metrics(truth, pred, scoring["noul_threshold"])}
            continue
        conf = [r["answers"][axis]["confidence"] for r in rows]
        if kind == "score":
            hits[axis] = within(scoring["score_tolerance"])
            axes[axis] = {"metrics": score_metrics(truth, pred, scoring["score_tolerance"]),
                          "confidence_buckets": confidence_table(truth, pred, conf, hits[axis])}
            continue
        hits[axis] = hit_equal
        axes[axis] = {"metrics": metrics(truth, pred, question["criteria"]),
                      "confidence_buckets": confidence_table(truth, pred, conf),
                      "prediction_counts": dict(Counter(pred))}
        for name, labels_by_axis in (annotators or {}).items():
            axes[axis]["agree_with_" + name] = agreement(
                {r["id"]: p for r, p in zip(rows, pred)}, labels_by_axis[axis])["correct"]
    axis = gate_config["axis"]
    report = {"axes": axes, "predictions": predictions}
    if axis in questions:
        kind = questions[axis]["type"]
        report["gate"] = {"axis": axis, **gate(
            [lookup[r["id"]][axis] for r in rows],
            [r["answers"][axis][kind] for r in rows],
            [r["answers"][axis]["confidence"] for r in rows],
            gate_config["confidence_floor"], gate_config["min_accuracy"], gate_config["min_coverage"],
            hit=hits[axis])}
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
    for record in records:
        request_bytes(record["state"], questions)  # Validate the entire batch before spending.
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
        if questions[config["axis"]]["type"] == "noul":
            raise ValueError("gate axis must be a Choice or Score question; Noul has no confidence")
        for field in ("confidence_floor", "min_accuracy", "min_coverage"):
            number(config[field], unit=True)
        if "labels_sha256" not in manifest:
            raise ValueError("evaluation requires a blind label commitment")
        scored_questions = {k: v for k, v in questions.items() if k in manifest.get("scored_axes", questions)}
        scoring = scoring_parameters(manifest, scored_questions)
    if manifest.get("mode") in ("confusion", "benchmark") and not fixture:
        raise ValueError("receipt-specific replay requires a pinned fixture")
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=False)  # Reserve before any paid request; failures remain reserved.
    completed = []
    for record in sendable:
        answer = client.ask(record["state"], questions)
        values = answer.project(questions)  # Typed fields only; never state, API extensions, or error text.
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
        computed = score(completed, labels, scored_questions, config, annotators, scoring)
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
