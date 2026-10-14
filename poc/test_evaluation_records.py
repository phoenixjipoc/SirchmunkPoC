"""Focused checks for audit-critical metrics and resumable grading; no API calls."""
import csv
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

import judge
from run_eval import score_retrieval, write_csv


class EvaluationRecordTests(unittest.TestCase):
    def test_multisource_any_hit_is_not_full_coverage(self):
        q={'gold_source_file':'one.pdf;two.pdf'}
        rec={'candidate_files':['/mnt/docs/S/one.pdf'],'sampled_files':['/mnt/docs/S/one.pdf'],
             'evidence_files':['/mnt/docs/S/one.pdf'],'evidence_found_files':[],'cited_files':[]}
        score=score_retrieval(q,rec)
        self.assertTrue(score['gold_in_evidence'])
        self.assertEqual(score['gold_coverage_evidence'],0.5)
        self.assertEqual(score['gold_coverage_found_evidence'],0)

    def test_reuse_citations_are_separate_from_fresh_retrieval(self):
        q={'gold_source_file':'one.pdf'}
        rec={'candidate_files':[],'sampled_files':[],'evidence_files':[],
             'cited_files':['/mnt/docs/S/one.pdf']}
        score=score_retrieval(q,rec)
        self.assertFalse(score['gold_in_candidates'])
        self.assertEqual(score['gold_coverage_cited'],1)

    def test_unanswerable_has_no_source_denominator(self):
        score=score_retrieval({'gold_source_file':''},{'candidate_files':[],'sampled_files':[],'evidence_files':[]})
        self.assertEqual(score['gold_coverage_cited'],'')

    def test_acceptance_is_in_prompt_and_answer_is_not_truncated(self):
        session=Mock()
        session.post.return_value.json.return_value={'choices':[{'message':{'content':'{"label":"correct","reason":"matches"}'}}],'usage':{'total_tokens':3}}
        answer='x'*13000+'END_OF_ANSWER'
        q={'question':'Q','type':'detail','gold_answer':'G','gold_passage':'P',
           'verify_note':'Old comparison | Acceptance: Examples are optional.'}
        label,reason,usage=judge.judge(session,{'base_url':'https://unused.invalid','model':'mock'},q,answer)
        prompt=session.post.call_args.kwargs['json']['messages'][0]['content']
        self.assertIn('Examples are optional.',prompt)
        self.assertNotIn('Old comparison',prompt)
        self.assertIn('END_OF_ANSWER',prompt)
        self.assertEqual(label,'correct')

    def test_invalid_judge_label_is_rejected(self):
        session=Mock()
        session.post.return_value.json.return_value={'choices':[{'message':{'content':'{"label":"correct","reason":"bad label for negative"}'}}]}
        with self.assertRaises(ValueError):
            judge.judge(session,{'base_url':'https://unused.invalid','model':'mock'},
                        {'question':'Q','type':'unanswerable','gold_answer':'NOT IN CORPUS','gold_passage':''},'I cannot confirm')


if __name__=='__main__': unittest.main()
