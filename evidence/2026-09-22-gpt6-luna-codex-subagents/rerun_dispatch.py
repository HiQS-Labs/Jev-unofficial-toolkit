"""Fresh Codex CLI sessions with mechanically exact stdin dispatch."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import importlib.util
import argparse

_spec = importlib.util.spec_from_file_location('luna_frozen', Path(__file__).with_name('gpt6_luna_subagent_evidence.py'))
h = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(h)

OPTIONS = ['exec', '--ignore-user-config', '-m', 'gpt-6-luna', '-c', 'model_reasoning_effort="medium"', '-c', 'model_provider="openai"', '-c', 'features.multi_agent=false', '-c', 'features.shell_tool=false', '-c', 'features.apps=false', '-c', 'features.plugins=false', '-c', 'features.unbounded_connection_retries=false', '-c', 'web_search="disabled"', '-s', 'read-only', '--json', '-']
EXCLUDED_ENV = {'OPENAI_API_KEY', 'CODEX_API_KEY', 'OPENAI_BASE_URL', 'OPENAI_FEDERATION_RULE_ID', 'OPENAI_IDENTITY_TOKEN_FILE'}


def launch(prompt, expected_sha256, target, cwd):
    if not isinstance(prompt, bytes) or hashlib.sha256(prompt).hexdigest() != expected_sha256:
        raise ValueError('Prompt bytes differ from frozen hash; process not started')
    target = Path(target)
    target.mkdir(parents=True, exist_ok=False)
    (target / 'prompt.txt').write_bytes(prompt)
    environment = {k: v for k, v in os.environ.items() if k not in EXCLUDED_ENV}
    argv = [shutil.which('codex') or 'codex', *OPTIONS]
    (target/'launch.json').write_text(json.dumps({'prompt_sha256': expected_sha256, 'argv': argv, 'cwd': str(Path(cwd).resolve()), 'destination': str(target.resolve()), 'excluded_env': sorted(EXCLUDED_ENV)}, sort_keys=True)+'\n')
    with (target/'events.jsonl').open('xb') as out, (target/'stderr.log').open('xb') as err:
        result = subprocess.run(argv, input=prompt, stdout=out, stderr=err, cwd=cwd, env=environment, timeout=120)
    (target/'exit-code.json').write_text(json.dumps({'returncode': result.returncode})+'\n')
    if result.returncode:
        raise RuntimeError('Codex process failed')


def attest(target, row, sessions):
    """Bind the exact plaintext runtime input, fresh session and final response."""
    target = Path(target)
    prompt = h.serialize_prompt(row).encode('utf-8')
    h.require(hashlib.sha256(prompt).hexdigest() == row['prompt_sha256'], 'frozen prompt mismatch')
    h.require((target/'prompt.txt').read_bytes() == prompt, 'dispatched prompt mismatch')
    launch_record = h.read(target/'launch.json')
    h.require(set(launch_record) == {'prompt_sha256', 'argv', 'cwd', 'destination', 'excluded_env'}, 'launch schema mismatch')
    h.require(launch_record['destination'] == str(target.resolve()) and launch_record['prompt_sha256'] == row['prompt_sha256'] and launch_record['argv'][1:] == OPTIONS
              and launch_record['excluded_env'] == sorted(EXCLUDED_ENV), 'dispatch configuration mismatch')
    h.require(h.read(target/'exit-code.json') == {'returncode': 0}, 'nonzero exit')
    events = h.rows(target/'events.jsonl')
    h.require(all(e['type'] in {'thread.started', 'turn.started', 'item.started', 'item.completed', 'turn.completed'} for e in events), 'CLI failure or unknown event')
    threads = [e for e in events if e['type'] == 'thread.started']
    completed = [e for e in events if e['type'] == 'turn.completed']
    h.require(len(threads) == len(completed) == sum(e['type'] == 'turn.started' for e in events) == 1, 'one fresh CLI turn required')
    session_id = threads[0]['thread_id']
    h.require(isinstance(session_id, str) and h.re.fullmatch('[a-zA-Z0-9-]+', session_id), 'invalid session id')
    items = [e['item'] for e in events if e['type'].startswith('item.')]
    h.require(all(i['type'] in {'agent_message', 'reasoning'} for i in items), 'CLI tool activity')
    finals = [i['text'] for e in events if e['type'] == 'item.completed' for i in [e['item']] if i['type'] == 'agent_message']
    h.require(len(finals) == 1 and events[-1]['type'] == 'turn.completed', 'CLI not finalized')
    traces = list(Path(sessions).glob('**/*' + session_id + '.jsonl'))
    h.require(len(traces) == 1, 'unique runtime trace required')
    trace_bytes = traces[0].read_bytes()
    trace = [h.loads(line) for line in trace_bytes.decode().splitlines() if line.strip()]
    h.require(all(r['type'] in {'session_meta', 'turn_context', 'response_item', 'event_msg', 'world_state', 'token_usage_record'} for r in trace), 'unknown runtime record')
    def payloads(kind):
        return [r['payload'] for r in trace if r['type'] == kind]
    metas, contexts = payloads('session_meta'), payloads('turn_context')
    h.require(len(metas) == len(contexts) == 1, 'session reuse or multiple turns')
    meta, context = metas[0], contexts[0]
    h.require(meta['cwd'] == context['cwd'] == launch_record['cwd'], 'runtime cwd mismatch')
    h.require(meta['id'] == session_id and meta['source'] == 'exec' and meta['model_provider'] == 'openai'
              and not meta.get('forked_from_id') and not meta.get('parent_thread_id'), 'fresh OpenAI exec required')
    h.require(context['model'] == 'gpt-6-luna' and context['effort'] == 'medium', 'resolved identity mismatch')
    settings = context['collaboration_mode']['settings']
    h.require(settings['model'] == 'gpt-6-luna' and settings['reasoning_effort'] == 'medium', 'settings identity mismatch')
    responses = payloads('response_item')
    h.require(all(r['type'] in {'message', 'reasoning'} for r in responses), 'runtime tool call')
    h.require(all(r.get('role') in {'user', 'developer', 'system', 'assistant'} for r in responses if r['type'] == 'message'), 'tool response role')
    # Scaffolding is recorded before the single turn_context. The task is the
    # sole user message after it; there is no encrypted-sidecar inference here.
    context_position = next(i for i, r in enumerate(trace) if r['type'] == 'turn_context')
    task_inputs = [r['payload'] for r in trace[context_position+1:] if r['type'] == 'response_item' and r['payload'].get('role') == 'user']
    h.require(len(task_inputs) == 1 and task_inputs[0]['content'] == [{'type': 'input_text', 'text': prompt.decode()}], 'actual runtime prompt differs')
    answer_items = [r for r in responses if r.get('role') == 'assistant' and r['type'] == 'message']
    h.require(len(answer_items) == 1 and answer_items[0].get('phase') == 'final_answer' and answer_items[0]['content'] == [{'type': 'output_text', 'text': finals[0]}], 'runtime final differs')
    runtime_events = payloads('event_msg')
    h.require(all(e['type'] in {'task_started', 'task_complete', 'item_started', 'item_completed', 'token_count', 'agent_reasoning'} for e in runtime_events), 'runtime failure or unknown event')
    for event in runtime_events:
        if event['type'] in {'item_started', 'item_completed'}:
            h.require(event['thread_id'] == session_id and event['turn_id'] == context['turn_id'], 'item identity mismatch')
            h.require(event['item']['type'] in {'UserMessage', 'AgentMessage', 'Reasoning'}, 'runtime tool item')
    starts = [e for e in runtime_events if e['type'] == 'task_started']
    ends = [e for e in runtime_events if e['type'] == 'task_complete']
    h.require(len(starts) == len(ends) == 1 and starts[0]['turn_id'] == ends[0]['turn_id'] == context['turn_id'], 'completion identity mismatch')
    h.require(trace[-1]['type'] == 'event_msg' and trace[-1]['payload'] == ends[0] and ends[0]['last_agent_message'] == finals[0], 'unfinished trace')
    usage_records = payloads('token_usage_record')
    h.require(len(usage_records) <= 1, 'multiple usage records')
    usage = usage_records[0]['usage'] if usage_records else None
    if usage_records:
        h.require(usage_records[0]['thread_id'] == session_id and usage_records[0]['turn_id'] == context['turn_id'], 'usage identity mismatch')
        h.validate_usage(usage)
        h.require(all(usage.get(k) == v for k, v in completed[0]['usage'].items()), 'CLI/runtime usage mismatch')
    with (target/'runtime.jsonl').open('xb') as stream:
        stream.write(trace_bytes)
    return dict(index=row['index'], choice=h.parse_choice(finals[0]), prompt_sha256=row['prompt_sha256'],
                agent_receipt_sha256=hashlib.sha256(trace_bytes).hexdigest(), agent_id_sha256=h.digest(session_id),
                launch_sha256=h.canonical_sha256(launch_record), model=context['model'], reasoning_effort=context['effort'],
                session_mode='fresh_exec', tool_calls=0, duration_ms=ends[0]['duration_ms'], usage=usage)


def preflight(blind_path, freeze_path):
    """Validate every frozen request and exact local runner before inference."""
    freeze = h.read(freeze_path)
    h.require(h.sha256_file(blind_path) == freeze['blind_sha256'], 'blind file drift')
    blind = h.rows(blind_path); h.validate_blind(blind, 100)
    prompts = [h.serialize_prompt(row).encode('utf-8') for row in blind]
    h.require(all(hashlib.sha256(p).hexdigest() == r['prompt_sha256'] for p, r in zip(prompts, blind)), 'preflight prompt drift')
    spec = importlib.util.spec_from_file_location('rerun_scoring', Path(__file__).with_name('rerun_scoring.py'))
    scorer = importlib.util.module_from_spec(spec); spec.loader.exec_module(scorer)
    scorer.validate_freeze(freeze)
    env = {k: v for k, v in os.environ.items() if k not in EXCLUDED_ENV}
    binary = shutil.which('codex') or 'codex'
    auth = subprocess.run([binary, 'login', 'status'], env=env, capture_output=True, timeout=15)
    h.require(auth.returncode == 0 and (auth.stdout + auth.stderr).decode().strip() == 'Logged in using ChatGPT', 'subscription authentication required')
    version = subprocess.run([binary, '--version'], env=env, capture_output=True, timeout=15)
    h.require(version.returncode == 0 and version.stdout.decode().strip() == 'codex-cli ' + freeze['codex_version'], 'Codex version drift')
    return scorer, freeze, blind, prompts


def run_attempt(blind_path, freeze_path, output, sessions, cwd):
    scorer, freeze, blind, prompts = preflight(blind_path, freeze_path)
    output = Path(output); output.mkdir(parents=True, exist_ok=False)
    h.write_results(output/'START.json', {'attempt':freeze['attempt'], 'freeze_sha256':h.sha256_file(freeze_path), 'rows':100})
    receipts = []
    try:
        for row, prompt in zip(blind, prompts):
            target = output / ('row-%03d' % row['index'])
            launch(prompt, row['prompt_sha256'], target, cwd)
            record = attest(target, row, sessions)
            scorer.validate_raw(receipts + [record], blind[:len(receipts)+1])
            h.write_results(target/'receipt.json', record)
            receipts.append(record)
            print(json.dumps({'attempt':freeze['attempt'], 'validated':len(receipts), 'total':100}), flush=True)
        with (output/'raw.jsonl').open('x') as stream:
            for record in receipts: stream.write(json.dumps(record, sort_keys=True) + '\n')
        h.write_results(output/'COMPLETE.json', {'attempt':freeze['attempt'], 'rows':100, 'raw_sha256':h.sha256_file(output/'raw.jsonl')})
    except BaseException as error:
        h.write_results(output/'STOP.json', {'attempt':freeze['attempt'], 'index':len(receipts), 'validated':len(receipts), 'failure_type':type(error).__name__, 'reason':str(error), 'scored':0})
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('blind', 'freeze', 'output', 'sessions', 'cwd'):
        parser.add_argument('--'+name, required=True, type=Path)
    args = parser.parse_args()
    run_attempt(args.blind, args.freeze, args.output, args.sessions, args.cwd)
