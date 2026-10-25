"""Checks for scoring edge cases and ranking isolation; no remote requests."""
import asyncio
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from analyze import hit,reciprocal,measure


class MetricChecks(unittest.TestCase):
    def test_unknown_before_positive_changes_bounds_not_known_hit(self):
        self.assertIsNone(hit([None,True],1))
        self.assertIs(hit([None,True],5),True)
        self.assertEqual(reciprocal([None,True]),(.5,1.0))

    def test_empty_and_error_stay_in_denominator(self):
        self.assertEqual(reciprocal([]),(0,0))
        self.assertEqual(measure([True,False,None]),dict(n=3,hits=1,unknown=1,lower_pct=33.33,upper_pct=66.67))

    def test_first_hit_at_cutoff(self):
        self.assertFalse(hit([False]*9+[True],5))
        self.assertTrue(hit([False]*9+[True],10))
        self.assertEqual(reciprocal([False]*9+[True]),(.1,.1))


class RerankChecks(unittest.IsolatedAsyncioTestCase):
    async def run_case(self,ordered):
        import experiment
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            (root/'baseline').mkdir(); (root/'inputs').mkdir()
            q=dict(id='X',question='Find the requested edition',type='detail',pair_id='')
            old=dict(references=[dict(file='b.pdf',path='/mnt/docs/S/b.pdf'),dict(file='a.pdf',path='/mnt/docs/S/a.pdf')],
                     keyword_files=['/mnt/docs/S/b.pdf','/mnt/docs/S/a.pdf'],directory_files=[])
            (root/'baseline/X.json').write_text(json.dumps(old))
            (root/'inputs/directory_scan.json').write_text(json.dumps({'candidates':[
                dict(filename='b.pdf',title='B'),dict(filename='a.pdf',title='A')]}))
            class Chat:
                records=[]
                async def achat(self,messages,**kwargs):
                    self.payload=json.loads(messages[1]['content'])
                    return SimpleNamespace(content=json.dumps({'ordered_files':ordered}))
            chat=Chat()
            r=await experiment.controlled(q,root,chat,'S')
            self.assertEqual([c['filename'] for c in chat.payload['candidates']],['a.pdf','b.pdf'])
            self.assertEqual(set(chat.payload),{'question','candidates'})
            return r

    async def test_exact_permutation_is_accepted(self):
        r=await self.run_case(['a.pdf','b.pdf'])
        self.assertEqual(r['status'],'ok')
        self.assertEqual([x['file'] for x in r['references']],['a.pdf','b.pdf'])

    async def test_invented_or_duplicate_candidates_are_rejected(self):
        r=await self.run_case(['a.pdf','invented.pdf'])
        self.assertEqual(r['status'],'technical_error')
        self.assertEqual(r['references'],[])
        r=await self.run_case(['a.pdf','a.pdf'])
        self.assertEqual(r['status'],'technical_error')


if __name__=='__main__': unittest.main()
