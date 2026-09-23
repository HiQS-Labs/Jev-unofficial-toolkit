import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / 'evidence/2026-09-22-gpt6-luna-codex-subagents/gpt6_luna_subagent_evidence.py'
spec = importlib.util.spec_from_file_location('luna_evidence', PATH)
helper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helper)


class EvidenceTests(unittest.TestCase):
    def test_duplicate_choice_is_rejected(self):
        with self.assertRaises(ValueError):
            helper.parse_choice('{"choice":"edit","choice":"read"}')

    def test_choice_boundary(self):
        for text in ('prose {"choice":"edit"}', '{"choice":"edit","extra":0}',
                     '{"choice":["edit","read"]}', '{"choice":"SENTINEL"}'):
            with self.subTest(text=text), self.assertRaises(ValueError):
                helper.parse_choice(text)
        self.assertEqual(helper.parse_choice('{"choice":"read"}'), 'read')




class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.paths = {name: self.root / (name + '.json') for name in
                      ('train', 'holdout', 'baselines', 'blind', 'raw', 'freeze', 'commitment', 'results', 'provenance', 'verification', 'child', 'parent')}
        self.dump_rows('train', [{'query': 'training synthetic', 'answers': [{'name': 'edit'}]}])
        self.dump_rows('holdout', [{'query': 'UNIQUE_SOURCE_SENTINEL ' + str(i), 'answers': [{'name': label}]} for i, label in enumerate(('edit', 'read'))])
        self.contract = dict(train_sha256=helper.sha256_file(self.paths['train']), holdout_sha256=helper.sha256_file(self.paths['holdout']),
                             train_rows=1, rows=2, support={label: int(label in ('edit', 'read')) for label in helper.LABELS}, baselines=dict(helper.CONTRACT['baselines']))
        self.baseline = dict(train_rows=1, holdout_rows=2, inputs={k: self.contract[k] for k in ('train_sha256', 'holdout_sha256')},
                             metrics={k: {'correct': v} for k, v in self.contract['baselines'].items()})
        self.dump('baselines', self.baseline)
        prepared = self.prepare()
        self.blind = helper.rows(self.paths['blind'])
        self.freeze = dict(prepared, schema='gh26-freeze-v1', support=self.contract['support'], baselines=self.contract['baselines'],
                           identity=helper.IDENTITY, needle_commit=helper.semif.NEEDLE_COMMIT, dataset_revision=helper.semif.DATASET_REVISION,
                           toolkit_base='a' * 40, toolkit_head='b' * 40, codex_version='0.116.0', model_catalog_sha256='c' * 64, concurrency=1)
        self.dump('freeze', self.freeze)
        self.raw = []
        for i in range(2):
            child, parent = self.trace(i)
            self.dump_rows('child', child); self.dump_rows('parent', parent)
            self.raw.append(helper.attest_trace(self.paths['child'], self.paths['parent'], self.blind[i], self.request(i)))
        self.dump_rows('raw', self.raw)

    def dump(self, name, value):
        self.paths[name].write_text(json.dumps(value))

    def dump_rows(self, name, value):
        self.paths[name].write_text(''.join(json.dumps(row) + '\n' for row in value))

    def prepare(self, contract=None, output=None):
        return helper.prepare(self.paths['train'], self.paths['holdout'], self.paths['baselines'], output or self.paths['blind'], contract=contract or self.contract)

    def request(self, i=0):
        return dict(task_name='row_%03d' % i, model='gpt-6-luna', reasoning_effort='medium', fork_turns='none', message=helper.serialize_prompt(self.blind[i]))

    def trace(self, i=0):
        task, session, turn = 'row_%03d' % i, 'child-%d' % i, 'turn-%d' % i
        choice = json.dumps({'choice': ('edit', 'search')[i]})
        def record(kind, **payload):
            return dict(type=kind, payload=payload)
        parent = [record('session_meta', id='parent'), record('session_meta', id='parent'),
                  record('response_item', type='function_call', namespace='collaboration', name='spawn_agent',
                         arguments=json.dumps(dict(task_name=task, model='gpt-6-luna', reasoning_effort='medium', fork_turns='none', message='PRIVATE_CIPHER')))]
        trace = [record('session_meta', id=session, model_provider='openai', source={'subagent': {'thread_spawn': dict(parent_thread_id='parent', depth=1, agent_path='/root/' + task)}}),
                 record('world_state', full=True, state={}),
                 record('event_msg', type='task_started', turn_id=turn),
                 record('turn_context', turn_id=turn, model='gpt-6-luna', effort='medium', collaboration_mode={'settings': {'model': 'gpt-6-luna', 'reasoning_effort': 'medium'}}),
                 record('inter_agent_communication_metadata', trigger_turn=True),
                 record('response_item', type='agent_message', author='/root', recipient='/root/' + task, content=[{'type': 'input_text', 'text': 'Message Type: NEW_TASK\nTask name: /root/' + task + '\nSender: /root\nPayload:\n'}, {'type': 'encrypted_content', 'encrypted_content': 'PRIVATE_CIPHER'}]),
                 record('event_msg', type='agent_message', phase='final_answer', message=choice),
                 record('response_item', type='message', role='assistant', phase='final_answer', content=[{'type': 'output_text', 'text': choice}]),
                 record('token_usage_record', thread_id=session, turn_id=turn, usage={'input_tokens': 10, 'output_tokens': 2}),
                 record('event_msg', type='token_count', info=None),
                 record('event_msg', type='task_complete', turn_id=turn, last_agent_message=choice, duration_ms=100)]
        return trace, parent

    def finalize(self):
        return helper.finalize_receipts(self.paths['blind'], self.paths['raw'], self.paths['freeze'], self.paths['commitment'], contract=self.contract)

    def summarize(self):
        return helper.summarize(*(self.paths[k] for k in ('holdout', 'blind', 'raw', 'freeze', 'commitment', 'results', 'provenance')), contract=self.contract)

    def verify(self):
        return helper.verify(*(self.paths[k] for k in ('results', 'provenance', 'freeze', 'commitment', 'verification')), contract=self.contract)

    def test_green_and_text_boundary_and_create_only(self):
        self.finalize(); self.summarize(); self.verify()
        for k in ('results', 'provenance', 'verification'):
            text = self.paths[k].read_text()
            for forbidden in ('UNIQUE_SOURCE_SENTINEL', 'PRIVATE_CIPHER', 'child-0', str(self.root)):
                self.assertNotIn(forbidden, text)
        with self.assertRaises(FileExistsError):
            self.finalize()
        with self.assertRaises(ValueError):
            self.summarize()
        with self.assertRaises(FileExistsError):
            self.verify()

    def test_prepare_bad_hashes_counts_support_baselines(self):
        import copy
        for key, value in [('train_sha256', '0' * 64), ('holdout_sha256', '0' * 64), ('train_rows', 3), ('rows', 3), ('support', {})]:
            contract = copy.deepcopy(self.contract); contract[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.prepare(contract, self.root / 'bad')
        for label in self.baseline['metrics']:
            report = copy.deepcopy(self.baseline); report['metrics'][label]['correct'] += 1
            self.dump('baselines', report)
            with self.subTest(baseline=label), self.assertRaises(ValueError):
                self.prepare(output=self.root / 'bad')

    def test_blind_schema_order_hash_and_options(self):
        import copy
        for key, value in [('index', 1), ('state', 'altered'), ('question', 'altered'), ('options', list(reversed(helper.OPTIONS))), ('prompt_sha256', '0' * 64), ('extra', 'SENTINEL')]:
            blind = copy.deepcopy(self.blind); blind[0][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                helper.validate_blind(blind, 2)
        expected = helper.QUESTION + '\nOptions in exact order:\n' + '\n'.join(o['id'] + ' — ' + o['description'] for o in helper.OPTIONS) + '\nState:\n' + self.blind[0]['state'] + helper.SUFFIX
        self.assertEqual(helper.serialize_prompt(self.blind[0]), expected)

    def test_trace_identity_model_effort_fork_nesting_tools_and_completion(self):
        import copy
        mutations = []
        for field, value in [('model', 'gpt-6-astra'), ('model', 'gpt-5.6-luna'), ('reasoning_effort', 'high'), ('fork_turns', 'all')]:
            def mutate(c, p, field=field, value=value):
                args = json.loads(p[-1]['payload']['arguments']); args[field] = value; p[-1]['payload']['arguments'] = json.dumps(args)
            mutations.append((field + str(value), mutate))
        mutations += [
            ('provider', lambda c, p: c[0]['payload'].update(model_provider='other')),
            ('extra-plaintext', lambda c, p: c[5]['payload']['content'].append({'type': 'input_text', 'text': 'EXTRA_INSTRUCTION_SENTINEL'})),
            ('altered-wrapper', lambda c, p: c[5]['payload']['content'][0].update(text='EXTRA_INSTRUCTION_SENTINEL')),
            ('extra-block-key', lambda c, p: c[5]['payload']['content'][1].update(text='EXTRA_INSTRUCTION_SENTINEL')),
            ('cipher-mismatch', lambda c, p: c[5]['payload']['content'][1].update(encrypted_content='other')),
            ('final-mismatch', lambda c, p: c[7]['payload']['content'][0].update(text='{"choice":"git"}')),
            ('runtime-model', lambda c, p: c[3]['payload'].update(model='SENTINEL')),
            ('runtime-effort', lambda c, p: c[3]['payload'].update(effort='high')),
            ('settings', lambda c, p: c[3]['payload']['collaboration_mode']['settings'].update(model='wrong')),
            ('nested-depth', lambda c, p: c[0]['payload']['source']['subagent']['thread_spawn'].update(depth=2)),
            ('wrong-parent', lambda c, p: c[0]['payload']['source']['subagent']['thread_spawn'].update(parent_thread_id='other')),
            ('wrong-path', lambda c, p: c[0]['payload']['source']['subagent']['thread_spawn'].update(agent_path='/root/row_001')),
            ('duplicate-turn', lambda c, p: c.insert(4, copy.deepcopy(c[3]))),
            ('duplicate-launch', lambda c, p: p.append(copy.deepcopy(p[-1]))),
            ('incomplete', lambda c, p: c.pop()),
            ('mismatched-turn', lambda c, p: c[-1]['payload'].update(turn_id='other')),
            ('extra-final', lambda c, p: c.insert(8, copy.deepcopy(c[7]))),
            ('descendant-agent', lambda c, p: c[5]['payload'].update(author='/root/row_000/nested')),
            ('unknown-event', lambda c, p: c.insert(9, {'type':'event_msg','payload':{'type':'spawn_agent'}})),
            ('tool-role', lambda c, p: c[7]['payload'].update(role='tool')),
            ('usage-string', lambda c, p: c[8]['payload']['usage'].update(input_tokens='SENTINEL')),
            ('usage-extra', lambda c, p: c[8]['payload']['usage'].update(secret='SENTINEL')),
            ('usage-identity', lambda c, p: c[8]['payload'].update(thread_id='other')),
            ('communication', lambda c, p: c[4]['payload'].update(trigger_turn=False)),
        ]
        for kind in ('function_call', 'custom_tool_call', 'computer_call', 'web_search_call', 'unknown'):
            mutations.append((kind, lambda c, p, kind=kind: c.insert(8, {'type':'response_item','payload':{'type':kind}})))
        for name, mutate in mutations:
            child, parent = self.trace(); mutate(child, parent)
            self.dump_rows('child', child); self.dump_rows('parent', parent)
            with self.subTest(name=name), self.assertRaises(ValueError):
                helper.attest_trace(self.paths['child'], self.paths['parent'], self.blind[0], self.request(0))

    def test_raw_allowed_fields_and_reuse(self):
        import copy
        for key in helper.RAW_FIELDS:
            raw = copy.deepcopy(self.raw); raw[0][key] = 'SENTINEL'
            with self.subTest(key=key), self.assertRaises(ValueError):
                helper.validate_raw(raw, self.blind)
        for key in ('agent_id_sha256', 'agent_receipt_sha256'):
            raw = copy.deepcopy(self.raw); raw[1][key] = raw[0][key]
            with self.subTest(reused=key), self.assertRaises(ValueError):
                helper.validate_raw(raw, self.blind)
        for raw in (self.raw[:1], self.raw[::-1], self.raw + self.raw[:1]):
            with self.assertRaises(ValueError):
                helper.validate_raw(raw, self.blind)
        raw = copy.deepcopy(self.raw); raw[0]['extra'] = 0
        with self.assertRaises(ValueError):
            helper.validate_raw(raw, self.blind)

    def test_production_missing_99_rows(self):
        blind = []
        for i in range(100):
            row = dict(self.blind[0], index=i); blind.append(row)
        helper.validate_blind(blind, 100)
        with self.assertRaises(ValueError):
            helper.validate_raw(self.raw * 49 + self.raw[:1], blind)

    def test_invalid_receipts_rejected_before_gold_open(self):
        from unittest.mock import patch
        self.finalize()
        self.paths['raw'].write_text(self.paths['raw'].read_text() + '\n')
        with patch.object(helper.semif, 'load_holdout', side_effect=AssertionError('gold opened')) as loader:
            with self.assertRaises(ValueError):
                self.summarize()
            loader.assert_not_called()
        self.assertFalse(self.paths['results'].exists())

    def test_missing_commitment_rejected_before_gold(self):
        from unittest.mock import patch
        with patch.object(helper.semif, 'load_holdout', side_effect=AssertionError('gold opened')) as loader:
            with self.assertRaises(FileNotFoundError):
                self.summarize()
            loader.assert_not_called()

    def test_freeze_all_metadata_fields_are_closed(self):
        import copy
        for key in helper.FREEZE_FIELDS:
            freeze = copy.deepcopy(self.freeze); freeze[key] = 'SENTINEL'
            with self.subTest(key=key), self.assertRaises(ValueError):
                helper.validate_freeze(freeze, contract=self.contract)
        freeze = copy.deepcopy(self.freeze); freeze['identity']['auth_mode'] = 'api_key'
        with self.assertRaises(ValueError):
            helper.validate_freeze(freeze, contract=self.contract)

    def test_metric_and_provenance_tampering(self):
        import copy
        self.finalize(); result, provenance = self.summarize()
        for key in result['metrics']:
            altered = copy.deepcopy(result); altered['metrics'][key] = 'SENTINEL'; self.dump('results', altered)
            with self.subTest(metric=key), self.assertRaises(ValueError):
                self.verify()
        self.dump('results', result)
        for key in provenance:
            altered = copy.deepcopy(provenance); altered[key] = 'SENTINEL'; self.dump('provenance', altered)
            with self.subTest(provenance=key), self.assertRaises(ValueError):
                self.verify()
        self.dump('provenance', provenance)
        altered = copy.deepcopy(result); altered['predictions'][0]['prompt_sha256'] = 'd' * 64; self.dump('results', altered)
        with self.assertRaises(ValueError):
            self.verify()
        self.assertFalse(self.paths['verification'].exists())

    def test_internal_reasoning_is_not_a_tool(self):
        child, parent = self.trace()
        child.insert(6, {'type': 'event_msg', 'payload': {'type': 'agent_reasoning', 'text': 'PRIVATE_REASONING_SENTINEL'}})
        child.insert(7, {'type': 'response_item', 'payload': {'type': 'reasoning', 'summary': []}})
        self.dump_rows('child', child); self.dump_rows('parent', parent)
        receipt = helper.attest_trace(self.paths['child'], self.paths['parent'], self.blind[0], self.request())
        self.assertEqual(receipt['tool_calls'], 0)
        self.assertNotIn('PRIVATE_REASONING_SENTINEL', json.dumps(receipt))

    def test_plaintext_launch_request_binding(self):
        child, parent = self.trace()
        self.dump_rows('child', child); self.dump_rows('parent', parent)
        for key, value in [('message', 'SENTINEL'), ('task_name', 'row_001'), ('extra', 0)]:
            request = self.request(); request[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                helper.attest_trace(self.paths['child'], self.paths['parent'], self.blind[0], request)


if __name__ == '__main__':
    unittest.main()
