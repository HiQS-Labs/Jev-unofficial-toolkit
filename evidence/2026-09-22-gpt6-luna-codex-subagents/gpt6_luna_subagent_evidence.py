#!/usr/bin/env python3
"""Receipt-local GH-26 preparation, scoring and independent verification.

Prompt hashes commit the requested plaintext; encrypted runtime task payloads
cannot prove delivered plaintext. Runtime logs attest execution, not provider identity.
"""
import argparse
import collections
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from jev.eval import metrics
from jev.guard import write_results

_spec = importlib.util.spec_from_file_location('semif_evidence', ROOT / 'evidence/2026-09-22-semif-six-action/semif_next_action.py')
semif = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(semif)
LABELS, OPTIONS, QUESTION = semif.LABELS, semif.OPTIONS, semif.QUESTION
sha256_file, canonical_sha256 = semif.sha256_file, semif.canonical_sha256
CONTRACT = dict(train_sha256=semif.TRAIN_SHA256, holdout_sha256=semif.HOLDOUT_SHA256,
                train_rows=500, rows=100, support=semif.SUPPORT, baselines=semif.BASELINES)
IDENTITY = dict(model='gpt-6-luna', reasoning_effort='medium', fork_turns='none',
                provider='codex', auth_mode='chatgpt_subscription')
SUFFIX = '\nReturn only one JSON object with exactly one key: {"choice":"<one exact label>"}. No prose or additional keys. Do not call any tools and do not delegate.'
USAGE = {'input_tokens', 'cached_input_tokens', 'cache_write_input_tokens', 'output_tokens', 'reasoning_output_tokens', 'total_tokens'}
RAW_FIELDS = {'index', 'task_name', 'agent_id_sha256', 'agent_receipt_sha256', 'launch_sha256',
              'prompt_sha256', 'model', 'reasoning_effort', 'fork_turns', 'tool_calls', 'choice', 'duration_ms', 'usage'}
PREDICTION_FIELDS = {'index', 'gold', 'choice', 'correct', 'prompt_sha256', 'agent_receipt_sha256'}
HASH_FIELDS = {'train_sha256', 'holdout_sha256', 'baselines_sha256', 'blind_sha256', 'helper_sha256'}
FREEZE_FIELDS = HASH_FIELDS | {'schema', 'rows', 'support', 'baselines', 'identity', 'needle_commit', 'dataset_revision',
                             'toolkit_base', 'toolkit_head', 'codex_version', 'model_catalog_sha256', 'concurrency'}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, 'duplicate JSON key')
        result[key] = value
    return result


def loads(text):
    return json.loads(text, object_pairs_hook=unique_object)


def read(path):
    return loads(Path(path).read_text())


def rows(path):
    # Reuse the established loader and additionally reject duplicate keys.
    values = semif.read_jsonl(path)
    for line in Path(path).read_text().splitlines():
        if line.strip():
            loads(line)
    return values


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


def is_hash(value):
    return isinstance(value, str) and re.fullmatch('[0-9a-f]{64}', value) is not None


def parse_choice(text):
    value = loads(text)
    require(isinstance(value, dict) and set(value) == {'choice'} and isinstance(value['choice'], str)
            and value['choice'] in LABELS, 'invalid child output')
    return value['choice']


def serialize_prompt(row):
    return QUESTION + '\nOptions in exact order:\n' + '\n'.join(
        option['id'] + ' — ' + option['description'] for option in OPTIONS) + '\nState:\n' + row['state'] + SUFFIX


def validate_blind(values, count):
    require(len(values) == count, 'blind count mismatch')
    for index, row in enumerate(values):
        require(set(row) == {'index', 'state', 'question', 'options', 'prompt_sha256'}, 'blind schema mismatch')
        require(type(row['index']) is int and row['index'] == index and isinstance(row['state'], str)
                and bool(row['state']) and row['question'] == QUESTION and row['options'] == list(OPTIONS), 'blind input drift')
        require(row['prompt_sha256'] == digest(serialize_prompt(row)), 'prompt hash mismatch')


def prepare(train_path, holdout_path, baselines_path, blind_path, *, contract=CONTRACT):
    require(sha256_file(train_path) == contract['train_sha256'], 'train hash mismatch')
    require(len(rows(train_path)) == contract['train_rows'], 'train row-count mismatch')
    holdout = semif.load_holdout(holdout_path, contract['holdout_sha256'], contract['rows'], contract['support'])
    if contract == CONTRACT:
        semif.validate_baselines(baselines_path)
    else:
        report = read(baselines_path)
        require(report['train_rows'] == contract['train_rows'] and report['holdout_rows'] == contract['rows'], 'baseline count mismatch')
        require(report['inputs'] == {key: contract[key] for key in ('train_sha256', 'holdout_sha256')}, 'baseline hashes mismatch')
        require({k: report['metrics'][k]['correct'] for k in contract['baselines']} == contract['baselines'], 'baseline mismatch')
    blind = []
    for index, row in enumerate(holdout):
        item = dict(index=index, state=row['query'], question=QUESTION, options=list(OPTIONS))
        item['prompt_sha256'] = digest(serialize_prompt(item))
        blind.append(item)
    validate_blind(blind, contract['rows'])
    with Path(blind_path).open('x', encoding='utf-8') as stream:
        for row in blind:
            stream.write(json.dumps(row, sort_keys=True, ensure_ascii=False) + '\n')
    return dict(rows=len(blind), train_sha256=sha256_file(train_path), holdout_sha256=sha256_file(holdout_path),
                baselines_sha256=sha256_file(baselines_path), blind_sha256=sha256_file(blind_path), helper_sha256=sha256_file(__file__))


def attest_trace(trace_path, parent_trace_path, blind_row, launch_request):
    """Read finalized local runtime artifacts; never publish their text or IDs."""
    child_bytes = Path(trace_path).read_bytes()
    trace = [loads(line) for line in child_bytes.decode().splitlines() if line.strip()]
    parent = rows(parent_trace_path)
    def payloads(kind):
        return [r['payload'] for r in trace if r['type'] == kind]
    meta, contexts = payloads('session_meta'), payloads('turn_context')
    require(len(meta) == len(contexts) == 1, 'one session and turn required')
    require(meta[0].get('model_provider') == 'openai', 'runtime provider mismatch')
    spawn = meta[0]['source']['subagent']['thread_spawn']
    task = 'row_{:03d}'.format(blind_row['index'])
    parent_meta = [r['payload'] for r in parent if r['type'] == 'session_meta']
    require(bool(parent_meta) and len({p['id'] for p in parent_meta}) == 1 and spawn['parent_thread_id'] == parent_meta[0]['id']
            and spawn['depth'] == 1 and spawn['agent_path'] == '/root/' + task, 'child parent/task binding mismatch')
    launches = []
    for record in parent:
        p = record.get('payload', {})
        if record['type'] == 'response_item' and p.get('type') == 'function_call' and p.get('name') == 'spawn_agent' and p.get('namespace') == 'collaboration':
            args = loads(p['arguments'])
            if args.get('task_name') == task:
                launches.append((record, args))
    require(len(launches) == 1, 'missing or repeated parent launch')
    launch, args = launches[0]
    require(set(launch_request) == {'task_name', 'model', 'reasoning_effort', 'fork_turns', 'message'}, 'launch request schema mismatch')
    require(launch_request['message'] == serialize_prompt(blind_row) and digest(launch_request['message']) == blind_row['prompt_sha256'], 'plaintext request commitment mismatch')
    require(all(launch_request[k] == args.get(k) for k in ('task_name', 'model', 'reasoning_effort', 'fork_turns')), 'launch request metadata mismatch')
    require(all(args.get(k) == IDENTITY[k] for k in ('model', 'reasoning_effort', 'fork_turns')), 'launch identity mismatch')
    context = contexts[0]
    settings = context.get('collaboration_mode', {}).get('settings', {})
    require(context.get('model') == IDENTITY['model'] and context.get('effort') == 'medium'
            and settings.get('model') == IDENTITY['model'] and settings.get('reasoning_effort') == 'medium', 'runtime identity mismatch')
    events = payloads('event_msg')
    starts = [p for p in events if p.get('type') == 'task_started']
    ends = [p for p in events if p.get('type') == 'task_complete']
    final = [p for p in events if p.get('type') == 'agent_message']
    require(len(starts) == len(ends) == len(final) == 1 and final[0].get('phase') == 'final_answer', 'incomplete or extra output')
    require(starts[0]['turn_id'] == ends[0]['turn_id'] == context['turn_id'], 'turn mismatch')
    require(trace[-1]['type'] == 'event_msg' and trace[-1]['payload'] == ends[0], 'trace not finalized')
    require(final[0]['message'] == ends[0]['last_agent_message'], 'final mismatch')
    require(all(p.get('type') in {'task_started', 'task_complete', 'agent_message', 'agent_reasoning', 'token_count'} for p in events), 'unexpected runtime event')
    responses = payloads('response_item')
    require(all(p.get('type') in {'message', 'agent_message', 'reasoning'} for p in responses), 'tool or unknown response item')
    require(all(p.get('role') in {'system', 'developer', 'user', 'assistant'} for p in responses if p.get('type') == 'message'), 'invalid message role')
    inbound = [p for p in responses if p.get('type') == 'agent_message']
    require(len(inbound) == 1 and inbound[0].get('author') == '/root' and inbound[0].get('recipient') == '/root/' + task, 'nested or additional task')
    wrapper = 'Message Type: NEW_TASK\nTask name: /root/' + task + '\nSender: /root\nPayload:\n'
    require(isinstance(args.get('message'), str) and inbound[0].get('content') == [
        {'type': 'input_text', 'text': wrapper},
        {'type': 'encrypted_content', 'encrypted_content': args['message']},
    ], 'inbound task content or encrypted correlation mismatch')
    assistant = [p for p in responses if p.get('role') == 'assistant']
    require(len(assistant) == 1 and assistant[0].get('phase') == 'final_answer', 'one assistant final required')
    require(assistant[0].get('content') == [{'type': 'output_text', 'text': final[0]['message']}], 'assistant final content mismatch')
    require(all(r['type'] in {'session_meta', 'turn_context', 'event_msg', 'response_item', 'world_state', 'inter_agent_communication_metadata', 'token_usage_record'} for r in trace), 'unknown trace event')
    communication = payloads('inter_agent_communication_metadata')
    require(communication == [{'trigger_turn': True}], 'unexpected communication metadata')
    require(len(payloads('world_state')) == 1, 'unexpected world-state count')
    usage_events = payloads('token_usage_record')
    require(len(usage_events) <= 1, 'multiple inference usage records')
    if usage_events:
        require(usage_events[0]['thread_id'] == meta[0]['id'] and usage_events[0]['turn_id'] == context['turn_id'], 'usage identity mismatch')
    usage = usage_events[0]['usage'] if usage_events else None
    result = dict(index=blind_row['index'], task_name=task, agent_id_sha256=digest(meta[0]['id']),
                  agent_receipt_sha256=hashlib.sha256(child_bytes).hexdigest(), launch_sha256=canonical_sha256(launch),
                  prompt_sha256=blind_row['prompt_sha256'], model=context['model'], reasoning_effort=context['effort'],
                  fork_turns=args['fork_turns'], tool_calls=0, choice=parse_choice(final[0]['message']),
                  duration_ms=ends[0]['duration_ms'], usage=usage)
    validate_raw([result], [blind_row], start=blind_row['index'])
    return result


def validate_raw(raw, blind, *, start=0):
    require(len(raw) == len(blind), 'receipt count mismatch')
    agents, traces = set(), set()
    for index, (row, source) in enumerate(zip(raw, blind), start):
        require(set(row) == RAW_FIELDS, 'raw schema mismatch')
        require(type(row['index']) is int and row['index'] == index and row['task_name'] == 'row_{:03d}'.format(index), 'row order mismatch')
        require(all(row[k] == IDENTITY[k] for k in ('model', 'reasoning_effort', 'fork_turns')) and type(row['tool_calls']) is int and row['tool_calls'] == 0, 'raw identity/tools mismatch')
        require(isinstance(row['choice'], str) and row['choice'] in LABELS, 'choice mismatch')
        require(all(is_hash(row[k]) for k in ('agent_id_sha256', 'agent_receipt_sha256', 'launch_sha256', 'prompt_sha256')), 'invalid digest')
        require(row['prompt_sha256'] == source['prompt_sha256'], 'request commitment mismatch')
        require(row['agent_id_sha256'] not in agents and row['agent_receipt_sha256'] not in traces, 'reused agent or receipt')
        agents.add(row['agent_id_sha256']); traces.add(row['agent_receipt_sha256'])
        require(type(row['duration_ms']) is int and row['duration_ms'] >= 0, 'invalid duration')
        usage = row['usage']
        require(usage is None or (isinstance(usage, dict) and set(usage) <= USAGE and bool(usage)
                and all(type(v) is int and v >= 0 for v in usage.values())), 'invalid usage')


def validate_freeze(freeze, *, contract=CONTRACT):
    require(set(freeze) == FREEZE_FIELDS, 'freeze schema mismatch')
    require(freeze['schema'] == 'gh26-freeze-v1' and freeze['identity'] == IDENTITY, 'freeze identity mismatch')
    require(all(is_hash(freeze[k]) for k in HASH_FIELDS | {'model_catalog_sha256'}), 'freeze hash mismatch')
    require(all(freeze[k] == contract[k] for k in ('train_sha256', 'holdout_sha256', 'rows', 'support', 'baselines')), 'frozen contract mismatch')
    require(freeze['helper_sha256'] == sha256_file(__file__), 'helper differs from freeze')
    require(freeze['needle_commit'] == semif.NEEDLE_COMMIT and freeze['dataset_revision'] == semif.DATASET_REVISION, 'source identity mismatch')
    require(all(isinstance(freeze[k], str) and re.fullmatch('[0-9a-f]{40}', freeze[k]) for k in ('toolkit_base', 'toolkit_head')), 'invalid toolkit revision')
    require(isinstance(freeze['codex_version'], str) and re.fullmatch(r'\d+\.\d+\.\d+(?:-[a-z]+\.\d+)?', freeze['codex_version']), 'invalid Codex version')
    require(type(freeze['concurrency']) is int and 1 <= freeze['concurrency'] <= 16, 'invalid concurrency')


def validate_usage(usage):
    require(usage is None or (isinstance(usage, dict) and set(usage) <= USAGE
            and all(type(v) is int and v >= 0 for v in usage.values())), 'invalid usage')


def response_projection(raw):
    return [{k: row[k] for k in ('index', 'choice', 'prompt_sha256', 'agent_receipt_sha256')} for row in raw]


def receipt_totals(raw):
    usage = None if any(r['usage'] is None for r in raw) else {
        k: sum(r['usage'][k] for r in raw)
        for k in sorted(set.intersection(*(set(r['usage']) for r in raw)))}
    return dict(duration_ms=sum(r['duration_ms'] for r in raw), usage=usage,
                responses_sha256=canonical_sha256(response_projection(raw)))


def validate_commitment(value, freeze_path, count):
    require(set(value) == {'schema', 'rows', 'raw_sha256', 'freeze_sha256', 'duration_ms', 'usage', 'responses_sha256'}
            and value['schema'] == 'gh26-raw-commitment-v1' and type(value['rows']) is int and value['rows'] == count
            and is_hash(value['raw_sha256']) and is_hash(value['responses_sha256'])
            and value['freeze_sha256'] == sha256_file(freeze_path), 'raw commitment mismatch')
    require(type(value['duration_ms']) is int and value['duration_ms'] >= 0, 'invalid committed timing')
    validate_usage(value['usage'])


def finalize_receipts(blind_path, raw_path, freeze_path, commitment_path, *, contract=CONTRACT):
    """Create the pre-label raw commitment. Called by the private coordinator."""
    freeze = read(freeze_path)
    validate_freeze(freeze, contract=contract)
    require(sha256_file(blind_path) == freeze['blind_sha256'], 'blind commitment mismatch')
    blind, raw = rows(blind_path), rows(raw_path)
    validate_blind(blind, contract['rows']); validate_raw(raw, blind)
    value = dict(schema='gh26-raw-commitment-v1', rows=len(raw), raw_sha256=sha256_file(raw_path),
                 freeze_sha256=sha256_file(freeze_path), **receipt_totals(raw))
    write_results(commitment_path, value)
    return value


def summarize(holdout_path, blind_path, raw_path, freeze_path, commitment_path, results_path, provenance_path, *, contract=CONTRACT):
    freeze, commitment = read(freeze_path), read(commitment_path)
    validate_freeze(freeze, contract=contract)
    validate_commitment(commitment, freeze_path, contract['rows'])
    require(sha256_file(blind_path) == freeze['blind_sha256'] and sha256_file(raw_path) == commitment['raw_sha256'], 'input commitment mismatch')
    blind, raw = rows(blind_path), rows(raw_path)
    validate_blind(blind, contract['rows']); validate_raw(raw, blind)
    require(all(commitment[k] == v for k, v in receipt_totals(raw).items()), 'raw totals commitment mismatch')
    # All receipts and pre-inference commitments are validated before opening gold.
    gold = semif.load_holdout(holdout_path, contract['holdout_sha256'], contract['rows'], contract['support'])
    require(all(b['state'] == g['query'] for b, g in zip(blind, gold)), 'state mismatch')
    predictions = [dict(index=i, gold=g['answers'][0]['name'], choice=r['choice'], correct=g['answers'][0]['name'] == r['choice'],
                        prompt_sha256=r['prompt_sha256'], agent_receipt_sha256=r['agent_receipt_sha256']) for i, (g, r) in enumerate(zip(gold, raw))]
    truth, choices = [p['gold'] for p in predictions], [p['choice'] for p in predictions]
    per_label = {l: dict(support=truth.count(l), predicted=choices.count(l), recall_correct=sum(t == c == l for t, c in zip(truth, choices)),
                        recall=sum(t == c == l for t, c in zip(truth, choices)) / truth.count(l) if truth.count(l) else None) for l in LABELS}
    result = dict(schema='gh26-results-v1', labels=list(LABELS), rows=len(raw), scored=len(raw), skipped=0,
                  metrics=metrics(truth, choices, LABELS), per_label=per_label, predictions=predictions)
    provenance = dict(schema='gh26-provenance-v1', freeze=freeze, freeze_sha256=sha256_file(freeze_path),
                      raw_commitment=commitment, raw_commitment_sha256=sha256_file(commitment_path),
                      duration_ms=commitment['duration_ms'], usage=commitment['usage'], cost=None,
                      prompt_binding='requested_plaintext_commitment_encrypted_delivery_unverified')
    for path in (results_path, provenance_path):
        require(not Path(path).exists(), 'output already exists')
    write_results(results_path, result); write_results(provenance_path, provenance)
    return result, provenance


def verify(results_path, provenance_path, freeze_path, commitment_path, output_path, *, contract=CONTRACT):
    result, provenance, freeze, commitment = map(read, (results_path, provenance_path, freeze_path, commitment_path))
    validate_freeze(freeze, contract=contract); validate_commitment(commitment, freeze_path, contract['rows'])
    require(set(provenance) == {'schema', 'freeze', 'freeze_sha256', 'raw_commitment', 'raw_commitment_sha256', 'duration_ms', 'usage', 'cost', 'prompt_binding'}, 'provenance schema mismatch')
    require(provenance['schema'] == 'gh26-provenance-v1' and provenance['freeze'] == freeze and provenance['freeze_sha256'] == sha256_file(freeze_path)
            and provenance['raw_commitment'] == commitment and provenance['raw_commitment_sha256'] == sha256_file(commitment_path)
            and provenance['duration_ms'] == commitment['duration_ms'] and provenance['usage'] == commitment['usage']
            and provenance['cost'] is None and provenance['prompt_binding'] == 'requested_plaintext_commitment_encrypted_delivery_unverified', 'provenance commitment mismatch')
    require(type(provenance['duration_ms']) is int and provenance['duration_ms'] >= 0, 'invalid timing')
    usage = provenance['usage']
    require(usage is None or (isinstance(usage, dict) and set(usage) <= USAGE and all(type(v) is int and v >= 0 for v in usage.values())), 'invalid usage')
    require(set(result) == {'schema', 'labels', 'rows', 'scored', 'skipped', 'metrics', 'per_label', 'predictions'}
            and result['schema'] == 'gh26-results-v1' and result['labels'] == list(LABELS)
            and result['rows'] == result['scored'] == contract['rows'] and result['skipped'] == 0, 'results schema mismatch')
    predictions = result['predictions']; require(len(predictions) == contract['rows'], 'incomplete result')
    matrix = [[0 for _ in LABELS] for _ in LABELS]; seen = set()
    for i, row in enumerate(predictions):
        require(set(row) == PREDICTION_FIELDS and type(row['index']) is int and row['index'] == i, 'prediction schema/order mismatch')
        require(row['gold'] in LABELS and row['choice'] in LABELS and type(row['correct']) is bool and row['correct'] == (row['gold'] == row['choice']), 'prediction labels mismatch')
        require(is_hash(row['prompt_sha256']) and is_hash(row['agent_receipt_sha256']) and row['agent_receipt_sha256'] not in seen, 'prediction digest mismatch')
        seen.add(row['agent_receipt_sha256']); matrix[LABELS.index(row['gold'])][LABELS.index(row['choice'])] += 1
    require(canonical_sha256(response_projection(predictions)) == commitment['responses_sha256'], 'response commitment mismatch')
    correct = sum(matrix[i][i] for i in range(6)); f1 = []; per_label = {}
    for i, label in enumerate(LABELS):
        actual, predicted, tp = sum(matrix[i]), sum(row[i] for row in matrix), matrix[i][i]
        f1.append(2 * tp / (actual + predicted) if actual + predicted else 0.0)
        per_label[label] = dict(support=actual, predicted=predicted, recall_correct=tp, recall=tp / actual if actual else None)
    independent = dict(labeled_n=len(predictions), uncertain_truth_n=0, correct=correct, raw_accuracy=correct / len(predictions),
                       macro_f1=sum(f1) / 6, confusion_labels=list(LABELS), confusion=matrix)
    require(result['metrics'] == independent and result['per_label'] == per_label, 'aggregate mismatch')
    require({k: v['support'] for k, v in per_label.items()} == contract['support'], 'support mismatch')
    value = dict(schema='gh26-verification-v1', verified=True, rows=len(predictions), metrics=independent,
                 results_sha256=sha256_file(results_path), provenance_sha256=sha256_file(provenance_path),
                 freeze_sha256=sha256_file(freeze_path), raw_commitment_sha256=sha256_file(commitment_path))
    write_results(output_path, value)
    return value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='operation', required=True)
    arguments = {'prepare': ('train', 'holdout', 'baselines', 'blind'),
                 'summarize': ('holdout', 'blind', 'raw', 'freeze', 'commitment', 'results', 'provenance'),
                 'verify': ('results', 'provenance', 'freeze', 'commitment', 'output')}
    for name, keys in arguments.items():
        command = sub.add_parser(name)
        for key in keys:
            command.add_argument('--' + key, required=True, type=Path)
    args = parser.parse_args()
    value = globals()[args.operation](*(getattr(args, k) for k in arguments[args.operation]))
    print(json.dumps(value if args.operation == 'prepare' else {'operation': args.operation, 'complete': True}, sort_keys=True))


if __name__ == '__main__':
    main()
