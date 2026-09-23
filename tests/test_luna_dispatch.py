"""Exact stdin dispatch boundary; no network or model calls."""
import hashlib
import copy
import json
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch, Mock

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('dispatch', ROOT / 'evidence/2026-09-22-gpt6-luna-codex-subagents/rerun_dispatch.py')
d = importlib.util.module_from_spec(spec)
spec.loader.exec_module(d)

class DispatchTests(unittest.TestCase):
    def test_bad_row_99_starts_no_process(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(d.subprocess,'run') as process:
            root=Path(folder); blind=[]
            for i in range(100):
                row={'index':i,'state':'synthetic','question':d.h.QUESTION,'options':list(d.h.OPTIONS)}
                row['prompt_sha256']=d.h.digest(d.h.serialize_prompt(row)); blind.append(row)
            blind[99]['state']='omitted-word corruption'
            path=root/'blind.jsonl';path.write_text(''.join(json.dumps(r)+'\n' for r in blind))
            freeze=root/'freeze.json';freeze.write_text(json.dumps({'blind_sha256':d.h.sha256_file(path)}))
            with self.assertRaisesRegex(ValueError,'prompt hash mismatch'):
                d.run_attempt(path,freeze,root/'attempt',root/'sessions',ROOT)
            process.assert_not_called()
            self.assertFalse((root/'attempt').exists())

    def test_attestation_failure_stops_attempt(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);freeze=root/'freeze';freeze.write_text('{}')
            blind=[{'index':i,'prompt_sha256':'a'*64} for i in range(2)]
            with patch.object(d,'preflight',return_value=(Mock(),{'attempt':1},blind,[b'x']*2)), \
                 patch.object(d,'launch') as launch, patch.object(d,'attest',side_effect=ValueError('bad trace')):
                with self.assertRaises(ValueError):d.run_attempt(root/'blind',freeze,root/'attempt',root/'sessions',ROOT)
                self.assertEqual(launch.call_count,1)
                self.assertEqual(json.loads((root/'attempt/STOP.json').read_text())['validated'],0)
                self.assertFalse((root/'attempt/COMPLETE.json').exists())

    def test_attempt_stops_without_retry_or_later_launch(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder); freeze=root/'freeze.json'; freeze.write_text('{}')
            blind=[{'index':i,'prompt_sha256':'a'*64} for i in range(3)]
            def launch_side_effect(prompt, digest, target, cwd):
                target.mkdir()
                if target.name == 'row-001': raise RuntimeError('synthetic stop')
            with patch.object(d,'preflight',return_value=(Mock(),{'attempt':1},blind,[b'x']*3)), \
                 patch.object(d,'launch',side_effect=launch_side_effect) as launch, \
                 patch.object(d,'attest',return_value={'index':0}):
                with self.assertRaises(RuntimeError):
                    d.run_attempt(root/'blind',freeze,root/'attempt',root/'sessions',ROOT)
                self.assertEqual(launch.call_count,2)
                self.assertEqual(json.loads((root/'attempt/STOP.json').read_text())['validated'],1)
                self.assertFalse((root/'attempt/row-002').exists())
                self.assertFalse((root/'attempt/raw.jsonl').exists())

    def test_exact_omitted_word_blocked_before_process(self):
        intended = b'predict the single best next broad action.'
        actual = intended.replace(b' next', b'')
        with tempfile.TemporaryDirectory() as folder, patch.object(d.subprocess, 'run') as run:
            with self.assertRaises(ValueError):
                d.launch(actual, hashlib.sha256(intended).hexdigest(), Path(folder)/'row', ROOT)
            run.assert_not_called()

    def test_exact_bytes_reach_stdin_and_no_shell(self):
        prompt = 'unchanged unicode — and a final period.'.encode()
        with tempfile.TemporaryDirectory() as folder, patch.object(d.subprocess, 'run', return_value=Mock(returncode=0)) as run:
            d.launch(prompt, hashlib.sha256(prompt).hexdigest(), Path(folder)/'row', ROOT)
            self.assertIs(run.call_args.kwargs['input'], prompt)
            self.assertFalse(run.call_args.kwargs.get('shell', False))
            self.assertEqual(run.call_args.args[0][-1], '-')
            self.assertIn('gpt-6-luna', run.call_args.args[0])
            self.assertNotIn('resume', run.call_args.args[0])
            self.assertNotIn('fork', run.call_args.args[0])

    def test_no_overwrite_and_no_process_retry(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(d.subprocess, 'run', return_value=Mock(returncode=1)) as run:
            target = Path(folder)/'row'
            with self.assertRaises(RuntimeError):
                d.launch(b'foo', hashlib.sha256(b'foo').hexdigest(), target, ROOT)
            self.assertEqual(run.call_count, 1)
            with self.assertRaises(FileExistsError):
                d.launch(b'foo', hashlib.sha256(b'foo').hexdigest(), target, ROOT)
            self.assertEqual(run.call_count, 1)

    def fixture(self, root):
        row = {'index': 0, 'state': 'SYNTHETIC_STATE'}
        prompt = d.h.serialize_prompt(row)
        row['prompt_sha256'] = d.h.digest(prompt)
        target = root/'row'; target.mkdir()
        (target/'prompt.txt').write_text(prompt)
        (target/'launch.json').write_text(json.dumps({'prompt_sha256': row['prompt_sha256'], 'argv': ['codex', *d.OPTIONS], 'cwd':str(root), 'destination':str(target.resolve()), 'excluded_env': sorted(d.EXCLUDED_ENV)}))
        (target/'exit-code.json').write_text('{"returncode":0}')
        final = '{"choice":"read"}'
        events = [{'type':'thread.started','thread_id':'session-1'}, {'type':'turn.started'},
                  {'type':'item.completed','item':{'type':'agent_message','text':final}}, {'type':'turn.completed','usage':{}}]
        (target/'events.jsonl').write_text(''.join(json.dumps(e)+'\n' for e in events))
        trace = [dict(type='session_meta', payload={'id':'session-1','source':'exec','model_provider':'openai','cwd':str(root)}),
                 dict(type='event_msg', payload={'type':'task_started','turn_id':'turn-1'}),
                 dict(type='turn_context',payload={'model':'gpt-6-luna','effort':'medium','turn_id':'turn-1','cwd':str(root),
                     'collaboration_mode':{'settings':{'model':'gpt-6-luna','reasoning_effort':'medium'}}}),
                 dict(type='response_item',payload={'type':'message','role':'user','content':[{'type':'input_text','text':prompt}]}),
                 dict(type='response_item',payload={'type':'message','role':'assistant','phase':'final_answer','content':[{'type':'output_text','text':final}]}),
                 dict(type='event_msg',payload={'type':'task_complete','turn_id':'turn-1','last_agent_message':final,'duration_ms':10})]
        sessions=root/'sessions';sessions.mkdir()
        return row, target, sessions, trace

    def test_runtime_exact_input_identity_tools_and_completion(self):
        mutations = [lambda t: t[3]['payload']['content'][0].update(text='changed input'),
                     lambda t: t[2]['payload'].update(model='other'),
                     lambda t: t[2]['payload'].update(effort='low'),
                     lambda t: t[0]['payload'].update(source='resume'),
                     lambda t: t.insert(4, {'type':'response_item','payload':{'type':'function_call','name':'exec'}}),
                     lambda t: t.insert(4, {'type':'response_item','payload':{'type':'message','role':'assistant','phase':'commentary','content':[{'type':'output_text','text':'extra prose'}]}}),
                     lambda t: t.pop(),
                     lambda t: t.append(copy.deepcopy(t[0]))]
        for mutate in [None, *mutations]:
            with self.subTest(mutation=mutate), tempfile.TemporaryDirectory() as folder:
                row, target, sessions, trace = self.fixture(Path(folder))
                if mutate: mutate(trace)
                (sessions/'trace-session-1.jsonl').write_text(''.join(json.dumps(t)+'\n' for t in trace))
                if mutate:
                    with self.assertRaises(ValueError): d.attest(target,row,sessions)
                else:
                    result=d.attest(target,row,sessions)
                    self.assertEqual(result['choice'],'read')
                    self.assertEqual(result['session_mode'],'fresh_exec')
