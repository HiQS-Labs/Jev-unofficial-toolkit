"""Synthetic controls for the separately authorized CLI attempts."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / 'evidence/2026-09-22-gpt6-luna-codex-subagents/rerun_scoring.py'
spec = importlib.util.spec_from_file_location('luna_rerun_scoring', PATH)
s = importlib.util.module_from_spec(spec)
spec.loader.exec_module(s)
ANCHOR_PATH = ROOT / 'evidence/2026-09-22-gpt6-luna-codex-subagents/rerun_anchored_verify.py'
anchor_spec = importlib.util.spec_from_file_location('luna_anchored_verify', ANCHOR_PATH)
anchored = importlib.util.module_from_spec(anchor_spec)
anchor_spec.loader.exec_module(anchored)


class ScoringTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.p = {k: self.root / (k + '.json') for k in ('blind', 'raw', 'holdout', 'freeze', 'commitment', 'results', 'provenance', 'verification')}
        self.blind, self.raw, gold = [], [], []
        for i, label in enumerate(('edit', 'read')):
            b = dict(index=i, state='SOURCE_SENTINEL_' + str(i), question=s.h.QUESTION, options=list(s.h.OPTIONS))
            b['prompt_sha256'] = s.h.digest(s.h.serialize_prompt(b)); self.blind.append(b)
            gold.append(dict(query=b['state'], answers=[dict(name=label)]))
            self.raw.append(dict(index=i, choice=label, prompt_sha256=b['prompt_sha256'], agent_receipt_sha256=s.h.digest('trace'+str(i)),
                                 agent_id_sha256=s.h.digest('session'+str(i)), launch_sha256=s.h.digest('launch'+str(i)),
                                 model='gpt-6-luna', reasoning_effort='medium', session_mode='fresh_exec', tool_calls=0,
                                 duration_ms=10, usage={'input_tokens': 100, 'output_tokens': 2}))
        for k, v in [('blind', self.blind), ('raw', self.raw), ('holdout', gold)]:self.write_rows(k, v)
        self.contract = dict(s.h.CONTRACT, rows=2, holdout_sha256=s.h.sha256_file(self.p['holdout']), support={l:int(l in ('edit','read')) for l in s.h.LABELS})
        self.freeze = dict(schema='gh26-cli-freeze-v1', attempt=1, rows=2, codex_version='0.155.0-alpha.16', auth_mode='chatgpt_subscription', blind_sha256=s.h.sha256_file(self.p['blind']),
                           dispatcher_sha256=s.h.sha256_file(s.DISPATCHER), scorer_sha256=s.h.sha256_file(s.__file__), old_helper_sha256=s.h.sha256_file(s.h.__file__),
                           support=self.contract['support'], baselines=self.contract['baselines'], needle_commit=s.h.semif.NEEDLE_COMMIT, dataset_revision=s.h.semif.DATASET_REVISION,
                           toolkit_head='a'*40, config_sha256=s.h.canonical_sha256({'options':s.dispatch.OPTIONS, 'excluded_env':sorted(s.dispatch.EXCLUDED_ENV)}), model='gpt-6-luna', reasoning_effort='medium', session_mode='fresh_exec', concurrency=1,
                           train_sha256=self.contract['train_sha256'], holdout_sha256=self.contract['holdout_sha256'], baselines_sha256='c'*64)
        self.write('freeze', self.freeze)

    def write(self, key, value):self.p[key].write_text(json.dumps(value))
    def write_rows(self, key, values):self.p[key].write_text(''.join(json.dumps(r)+'\n' for r in values))
    def finalize(self):return s.finalize(*(self.p[k] for k in ('blind','raw','freeze','commitment')), contract=self.contract)
    def summarize(self):return s.summarize(*(self.p[k] for k in ('holdout','blind','raw','freeze','commitment','results','provenance')), contract=self.contract)
    def verify(self):return s.verify(*(self.p[k] for k in ('results','provenance','freeze','commitment','verification')), contract=self.contract)

    def test_reused_session_fails(self):
        self.raw[1]['agent_id_sha256'] = self.raw[0]['agent_id_sha256']
        with self.assertRaises(ValueError):s.validate_raw(self.raw, self.blind)

    def test_green_text_boundary_and_create_only(self):
        self.finalize(); self.summarize(); self.verify()
        for key in ('results','provenance','verification'):
            self.assertNotIn('SOURCE_SENTINEL', self.p[key].read_text())
            self.assertNotIn(str(self.root), self.p[key].read_text())
        with self.assertRaises(FileExistsError):self.finalize()
        with self.assertRaises(ValueError):self.summarize()
        with self.assertRaises(FileExistsError):self.verify()

    def test_raw_closed_fields_order_identity_usage(self):
        for key in s.RAW_FIELDS:
            raw = copy.deepcopy(self.raw);raw[0][key]='SOURCE_SENTINEL'
            with self.subTest(key=key), self.assertRaises(ValueError):s.validate_raw(raw,self.blind)
        for key in ('agent_receipt_sha256','launch_sha256'):
            raw=copy.deepcopy(self.raw);raw[1][key]=raw[0][key]
            with self.subTest(reused=key), self.assertRaises(ValueError):s.validate_raw(raw,self.blind)
        for raw in (self.raw[:1],self.raw[::-1],self.raw+self.raw[:1]):
            with self.assertRaises(ValueError):s.validate_raw(raw,self.blind)
        for value in ({'input_tokens':True},{'input_tokens':-1},{'source':'SOURCE_SENTINEL'}):
            raw=copy.deepcopy(self.raw);raw[0]['usage']=value
            with self.assertRaises(ValueError):s.validate_raw(raw,self.blind)

    def test_duplicate_prompt_rows_keep_distinct_sessions(self):
        blind, raw = copy.deepcopy(self.blind), copy.deepcopy(self.raw)
        blind[1] = dict(blind[0], index=1)
        raw[1]['prompt_sha256'] = raw[0]['prompt_sha256']
        self.assertEqual(blind[0]['prompt_sha256'], blind[1]['prompt_sha256'])
        for key in ('launch_sha256', 'agent_id_sha256', 'agent_receipt_sha256'):
            self.assertNotEqual(raw[0][key], raw[1][key])
        s.h.validate_blind(blind, 2)
        s.validate_raw(raw, blind)
        self.assertEqual(len(raw), 2)

    def test_freeze_fields_and_attempt_limit(self):
        for key in s.FREEZE_FIELDS:
            freeze=copy.deepcopy(self.freeze);freeze[key]='SOURCE_SENTINEL'
            with self.subTest(key=key), self.assertRaises(ValueError):s.validate_freeze(freeze,contract=self.contract)
        for attempt in (0,4,True):
            freeze=copy.deepcopy(self.freeze);freeze['attempt']=attempt
            with self.assertRaises(ValueError):s.validate_freeze(freeze,contract=self.contract)
        for attempt in (1,2,3):
            freeze=copy.deepcopy(self.freeze);freeze['attempt']=attempt
            s.validate_freeze(freeze,contract=self.contract)

    def test_bad_raw_and_blind_before_gold(self):
        self.finalize()
        for key in ('raw','blind'):
            old=self.p[key].read_text();self.p[key].write_text(old+'\n')
            with patch.object(s.h.semif,'load_holdout',side_effect=AssertionError('opened gold')) as load:
                with self.assertRaises(ValueError):self.summarize()
                load.assert_not_called()
            self.p[key].write_text(old)
        self.assertFalse(self.p['results'].exists())

    def test_missing_commitment_before_gold(self):
        with patch.object(s.h.semif,'load_holdout',side_effect=AssertionError('opened gold')) as load:
            with self.assertRaises(FileNotFoundError):self.summarize()
            load.assert_not_called()

    def test_99_is_incomplete(self):
        blind=[dict(self.blind[0],index=i) for i in range(100)]
        with self.assertRaises(ValueError):s.validate_raw(self.raw*49+self.raw[:1],blind)

    def test_tampered_metrics_metadata_and_prediction(self):
        self.finalize();result,provenance=self.summarize()
        for key in result['metrics']:
            changed=copy.deepcopy(result);changed['metrics'][key]='SOURCE_SENTINEL';self.write('results',changed)
            with self.subTest(metric=key),self.assertRaises(ValueError):self.verify()
        self.write('results',result)
        for key in provenance:
            changed=copy.deepcopy(provenance);changed[key]='SOURCE_SENTINEL';self.write('provenance',changed)
            with self.subTest(provenance=key),self.assertRaises(ValueError):self.verify()
        self.write('provenance',provenance)
        changed=copy.deepcopy(result);changed['predictions'][0]['choice']='read';changed['predictions'][0]['correct']=False
        self.write('results',changed)
        with self.assertRaises(ValueError):self.verify()
        self.assertFalse(self.p['verification'].exists())

    def test_anchor_rejects_coherent_bundle_replacement(self):
        self.finalize();result,provenance=self.summarize()
        changed=copy.deepcopy(result);changed['predictions'][0]['choice']='read';changed['predictions'][0]['correct']=False
        truth=[row['gold'] for row in changed['predictions']];choices=[row['choice'] for row in changed['predictions']]
        changed['metrics']=s.metrics(truth,choices,s.h.LABELS)
        changed['per_label']={label:dict(support=truth.count(label),predicted=choices.count(label),
            recall_correct=sum(t==c==label for t,c in zip(truth,choices)),
            recall=sum(t==c==label for t,c in zip(truth,choices))/truth.count(label) if truth.count(label) else None)
            for label in s.h.LABELS}
        commitment=s.h.read(self.p['commitment'])
        commitment['responses_sha256']=s.h.canonical_sha256(s.h.response_projection(changed['predictions']))
        self.write('commitment',commitment)
        provenance['raw_commitment']=commitment
        provenance['raw_commitment_sha256']=s.h.sha256_file(self.p['commitment'])
        self.write('results',changed);self.write('provenance',provenance)
        self.assertTrue(self.verify()['verified'])
        output=self.root/'anchored-verification.json'
        with self.assertRaises(ValueError):
            anchored.verify(*(self.p[k] for k in ('results','provenance','freeze','commitment')),output)
        self.assertFalse(output.exists())

    def test_anchor_accepts_published_commitment(self):
        attempt=ROOT/'evidence/2026-09-22-gpt6-luna-codex-subagents/rerun-attempt-1'
        output=self.root/'anchored-verification.json'
        value=anchored.verify(*(attempt/name for name in ('results.json','provenance.json','freeze.json','raw-commitment.json')),output)
        self.assertTrue(value['verified'])
        self.assertEqual(value['raw_commitment_sha256'],anchored.RAW_COMMITMENT_SHA256)

    def test_duplicate_json_keys_fail(self):
        self.p['raw'].write_text('{"index":0,"index":1}\n')
        with self.assertRaises(ValueError):s.h.rows(self.p['raw'])


if __name__=='__main__':unittest.main()
