#!/usr/bin/env python3
"""Closed receipts for the separately authorized fresh CLI execution attempts."""
import argparse
import importlib.util
from pathlib import Path
import re

_spec = importlib.util.spec_from_file_location('original_luna', Path(__file__).with_name('gpt6_luna_subagent_evidence.py'))
h = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(h)
from jev.eval import metrics
from jev.guard import write_results

DISPATCHER = Path(__file__).with_name('rerun_dispatch.py')
_dispatch_spec = importlib.util.spec_from_file_location('cli_dispatch', DISPATCHER)
dispatch = importlib.util.module_from_spec(_dispatch_spec)
_dispatch_spec.loader.exec_module(dispatch)
IDENTITY = dict(model='gpt-6-luna', reasoning_effort='medium', session_mode='fresh_exec')
RAW_FIELDS = {'index', 'choice', 'prompt_sha256', 'agent_receipt_sha256', 'agent_id_sha256',
              'launch_sha256', 'model', 'reasoning_effort', 'session_mode', 'tool_calls', 'duration_ms', 'usage'}
FREEZE_HASHES = {'blind_sha256', 'dispatcher_sha256', 'scorer_sha256', 'old_helper_sha256', 'config_sha256',
                 'train_sha256', 'holdout_sha256', 'baselines_sha256'}
FREEZE_FIELDS = FREEZE_HASHES | {'schema', 'attempt', 'rows', 'toolkit_head', 'model', 'reasoning_effort',
                               'session_mode', 'concurrency', 'support', 'baselines', 'needle_commit', 'dataset_revision', 'codex_version', 'auth_mode'}
COMMITMENT_FIELDS = {'schema', 'attempt', 'rows', 'raw_sha256', 'freeze_sha256', 'duration_ms', 'usage', 'responses_sha256'}
RESULT_FIELDS = {'schema', 'attempt', 'labels', 'rows', 'scored', 'skipped', 'metrics', 'per_label', 'predictions'}
PROVENANCE_FIELDS = {'schema', 'freeze', 'freeze_sha256', 'raw_commitment', 'raw_commitment_sha256', 'duration_ms', 'usage', 'cost'}


def validate_raw(raw, blind):
    h.require(len(raw) == len(blind) and bool(raw), 'incomplete raw receipts')
    seen = {key: set() for key in ('agent_receipt_sha256', 'agent_id_sha256', 'launch_sha256')}
    for i, (row, source) in enumerate(zip(raw, blind)):
        h.require(set(row) == RAW_FIELDS and type(row['index']) is int and row['index'] == i, 'raw schema/order mismatch')
        h.require(all(row[k] == v for k, v in IDENTITY.items()) and type(row['tool_calls']) is int and row['tool_calls'] == 0, 'identity/tool mismatch')
        h.require(isinstance(row['choice'], str) and row['choice'] in h.LABELS, 'invalid choice')
        h.require(h.is_hash(row['prompt_sha256']) and row['prompt_sha256'] == source['prompt_sha256'], 'prompt mismatch')
        for key, values in seen.items():
            h.require(h.is_hash(row[key]) and row[key] not in values, 'invalid/reused receipt identity')
            values.add(row[key])
        h.require(type(row['duration_ms']) is int and row['duration_ms'] >= 0, 'invalid duration')
        h.validate_usage(row['usage'])


def validate_freeze(freeze, *, contract=h.CONTRACT):
    h.require(set(freeze) == FREEZE_FIELDS and freeze['schema'] == 'gh26-cli-freeze-v1', 'freeze schema mismatch')
    h.require(type(freeze['attempt']) is int and 1 <= freeze['attempt'] <= 3, 'attempt outside authorization')
    h.require(type(freeze['rows']) is int and freeze['rows'] == contract['rows']
              and type(freeze['concurrency']) is int and freeze['concurrency'] == 1, 'freeze count/concurrency mismatch')
    h.require(all(freeze[k] == v for k, v in IDENTITY.items()), 'freeze identity mismatch')
    h.require(freeze['codex_version'] == '0.155.0-alpha.16' and freeze['auth_mode'] == 'chatgpt_subscription', 'CLI version/auth mismatch')
    h.require(all(h.is_hash(freeze[k]) for k in FREEZE_HASHES), 'invalid freeze hash')
    h.require(freeze['config_sha256'] == h.canonical_sha256({'options': dispatch.OPTIONS, 'excluded_env': sorted(dispatch.EXCLUDED_ENV)}), 'dispatch config commitment mismatch')
    h.require(all(freeze[k] == contract[k] for k in ('train_sha256', 'holdout_sha256', 'support', 'baselines')), 'frozen dataset mismatch')
    h.require(freeze['needle_commit'] == h.semif.NEEDLE_COMMIT and freeze['dataset_revision'] == h.semif.DATASET_REVISION, 'dataset revision mismatch')
    h.require(isinstance(freeze['toolkit_head'], str) and re.fullmatch('[0-9a-f]{40}', freeze['toolkit_head']), 'invalid toolkit revision')
    h.require(freeze['dispatcher_sha256'] == h.sha256_file(DISPATCHER) and freeze['scorer_sha256'] == h.sha256_file(__file__)
              and freeze['old_helper_sha256'] == h.sha256_file(h.__file__), 'frozen helper drift')


def validate_commitment(commitment, freeze_path, freeze):
    h.require(set(commitment) == COMMITMENT_FIELDS and commitment['schema'] == 'gh26-cli-commitment-v1', 'commitment schema mismatch')
    h.require(type(commitment['rows']) is int and commitment['rows'] == freeze['rows']
              and type(commitment['attempt']) is int and commitment['attempt'] == freeze['attempt'], 'commitment attempt/count mismatch')
    h.require(commitment['freeze_sha256'] == h.sha256_file(freeze_path)
              and h.is_hash(commitment['raw_sha256']) and h.is_hash(commitment['responses_sha256']), 'commitment hash mismatch')
    h.require(type(commitment['duration_ms']) is int and commitment['duration_ms'] >= 0, 'invalid committed duration')
    h.validate_usage(commitment['usage'])


def _inputs(blind_path, raw_path, freeze_path, contract):
    freeze = h.read(freeze_path); validate_freeze(freeze, contract=contract)
    h.require(h.sha256_file(blind_path) == freeze['blind_sha256'], 'blind commitment mismatch')
    blind, raw = h.rows(blind_path), h.rows(raw_path)
    h.validate_blind(blind, contract['rows']); validate_raw(raw, blind)
    return freeze, blind, raw


def finalize(blind_path, raw_path, freeze_path, commitment_path, *, contract=h.CONTRACT):
    """Create the complete receipt commitment before the scorer can open gold."""
    freeze, _, raw = _inputs(blind_path, raw_path, freeze_path, contract)
    value = dict(schema='gh26-cli-commitment-v1', attempt=freeze['attempt'], rows=len(raw),
                 raw_sha256=h.sha256_file(raw_path), freeze_sha256=h.sha256_file(freeze_path), **h.receipt_totals(raw))
    write_results(commitment_path, value)
    return value


def summarize(holdout_path, blind_path, raw_path, freeze_path, commitment_path, results_path, provenance_path, *, contract=h.CONTRACT):
    commitment = h.read(commitment_path)
    freeze, blind, raw = _inputs(blind_path, raw_path, freeze_path, contract)
    validate_commitment(commitment, freeze_path, freeze)
    h.require(commitment['raw_sha256'] == h.sha256_file(raw_path)
              and all(commitment[k] == v for k, v in h.receipt_totals(raw).items()), 'finalized raw mismatch')
    # No gold file is opened before every receipt and commitment passes.
    gold = h.semif.load_holdout(holdout_path, contract['holdout_sha256'], contract['rows'], contract['support'])
    h.require(all(b['state'] == g['query'] for b, g in zip(blind, gold)), 'blind/gold state mismatch')
    predictions = [dict(index=i, gold=g['answers'][0]['name'], choice=r['choice'], correct=g['answers'][0]['name'] == r['choice'],
                        prompt_sha256=r['prompt_sha256'], agent_receipt_sha256=r['agent_receipt_sha256']) for i, (g, r) in enumerate(zip(gold, raw))]
    truth, choices = [r['gold'] for r in predictions], [r['choice'] for r in predictions]
    per_label = {label: dict(support=truth.count(label), predicted=choices.count(label),
                            recall_correct=sum(t == c == label for t, c in zip(truth, choices)),
                            recall=sum(t == c == label for t, c in zip(truth, choices)) / truth.count(label) if truth.count(label) else None) for label in h.LABELS}
    result = dict(schema='gh26-cli-results-v1', attempt=freeze['attempt'], labels=list(h.LABELS), rows=len(raw), scored=len(raw), skipped=0,
                  metrics=metrics(truth, choices, h.LABELS), per_label=per_label, predictions=predictions)
    provenance = dict(schema='gh26-cli-provenance-v1', freeze=freeze, freeze_sha256=h.sha256_file(freeze_path),
                      raw_commitment=commitment, raw_commitment_sha256=h.sha256_file(commitment_path),
                      duration_ms=commitment['duration_ms'], usage=commitment['usage'], cost=None)
    h.require(not Path(results_path).exists() and not Path(provenance_path).exists(), 'results already exist')
    write_results(results_path, result); write_results(provenance_path, provenance)
    return result, provenance


def verify(results_path, provenance_path, freeze_path, commitment_path, output_path, *, contract=h.CONTRACT):
    """Independently recalculate aggregates and bind the pre-label commitments."""
    result, provenance, freeze, commitment = map(h.read, (results_path, provenance_path, freeze_path, commitment_path))
    validate_freeze(freeze, contract=contract); validate_commitment(commitment, freeze_path, freeze)
    expected_provenance = dict(schema='gh26-cli-provenance-v1', freeze=freeze, freeze_sha256=h.sha256_file(freeze_path),
                               raw_commitment=commitment, raw_commitment_sha256=h.sha256_file(commitment_path),
                               duration_ms=commitment['duration_ms'], usage=commitment['usage'], cost=None)
    h.require(set(provenance) == PROVENANCE_FIELDS and provenance == expected_provenance, 'provenance differs from commitments')
    h.require(set(result) == RESULT_FIELDS and result['schema'] == 'gh26-cli-results-v1'
              and type(result['attempt']) is int and result['attempt'] == freeze['attempt'] and result['labels'] == list(h.LABELS), 'result schema mismatch')
    h.require(type(result['rows']) is int and type(result['scored']) is int and type(result['skipped']) is int
              and result['rows'] == result['scored'] == contract['rows'] and result['skipped'] == 0, 'result count mismatch')
    predictions = result['predictions']; h.require(isinstance(predictions, list) and len(predictions) == contract['rows'], 'incomplete predictions')
    matrix = [[0] * len(h.LABELS) for _ in h.LABELS]; seen = set()
    for i, row in enumerate(predictions):
        h.require(set(row) == h.PREDICTION_FIELDS and type(row['index']) is int and row['index'] == i, 'prediction order/schema mismatch')
        h.require(row['gold'] in h.LABELS and row['choice'] in h.LABELS and type(row['correct']) is bool
                  and row['correct'] == (row['gold'] == row['choice']), 'prediction labels mismatch')
        h.require(h.is_hash(row['prompt_sha256']) and h.is_hash(row['agent_receipt_sha256']) and row['agent_receipt_sha256'] not in seen, 'prediction digest mismatch')
        seen.add(row['agent_receipt_sha256']); matrix[h.LABELS.index(row['gold'])][h.LABELS.index(row['choice'])] += 1
    h.require(h.canonical_sha256(h.response_projection(predictions)) == commitment['responses_sha256'], 'response commitment mismatch')
    f1, per_label = [], {}
    for i, label in enumerate(h.LABELS):
        actual, predicted, tp = sum(matrix[i]), sum(row[i] for row in matrix), matrix[i][i]
        f1.append(2 * tp / (actual + predicted) if actual + predicted else 0.0)
        per_label[label] = dict(support=actual, predicted=predicted, recall_correct=tp, recall=tp / actual if actual else None)
    correct = sum(matrix[i][i] for i in range(len(h.LABELS)))
    independent = dict(labeled_n=len(predictions), uncertain_truth_n=0, correct=correct, raw_accuracy=correct / len(predictions),
                       macro_f1=sum(f1) / len(h.LABELS), confusion_labels=list(h.LABELS), confusion=matrix)
    h.require(result['metrics'] == independent and result['per_label'] == per_label, 'aggregate mismatch')
    h.require({k:v['support'] for k,v in per_label.items()} == contract['support'], 'support mismatch')
    value = dict(schema='gh26-cli-verification-v1', verified=True, attempt=freeze['attempt'], rows=len(predictions), metrics=independent,
                 results_sha256=h.sha256_file(results_path), provenance_sha256=h.sha256_file(provenance_path),
                 freeze_sha256=h.sha256_file(freeze_path), raw_commitment_sha256=h.sha256_file(commitment_path))
    write_results(output_path, value)
    return value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='operation', required=True)
    operations = {'finalize': ('blind','raw','freeze','commitment'),
                  'summarize': ('holdout','blind','raw','freeze','commitment','results','provenance'),
                  'verify': ('results','provenance','freeze','commitment','output')}
    for operation, keys in operations.items():
        command = commands.add_parser(operation)
        for key in keys:command.add_argument('--'+key, type=Path, required=True)
    args = parser.parse_args()
    globals()[args.operation](*(getattr(args,key) for key in operations[args.operation]))
    print('Completed '+args.operation)


if __name__ == '__main__':
    main()
