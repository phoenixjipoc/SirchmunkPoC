"""Offline safety and evidence-integrity checks; run inside the same container."""
import asyncio
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from runtime import CheckedChat, ModelMismatch, RawSampler, RetrievalOnly, phase_call
from sirchmunk.learnings.evidence_processor import SampleWindow


class RuntimeChecks(unittest.IsolatedAsyncioTestCase):
    async def test_raw_response_mismatch_stops_even_if_caller_catches(self):
        async def wrong_response(*args,**kwargs):
            return SimpleNamespace(model='wrong-model',id='test',usage=None,choices=[],_request_id='test')
        with tempfile.TemporaryDirectory() as tmp, patch('openai.resources.chat.completions.AsyncCompletions.create',wrong_response):
            chat=CheckedChat('gpt-6-sol',Path(tmp)/'calls.jsonl',Path(tmp)/'STOP')
            with self.assertRaises(ModelMismatch):
                await phase_call('keywords',chat._async_client.chat.completions.create(model='gpt-6-sol',messages=[],stream=False))
            with self.assertRaises(ModelMismatch):
                chat.ensure_running()
            self.assertEqual(chat.records[0]['response_model'],'wrong-model')
            await chat.close()

    async def test_missing_model_is_not_replaced_with_requested_model(self):
        with tempfile.TemporaryDirectory() as tmp:
            chat=CheckedChat('gpt-6-sol',Path(tmp)/'calls.jsonl',Path(tmp)/'STOP')
            with self.assertRaises(ModelMismatch):
                chat.check(None,'raw_response')
            await chat.close()

    async def test_raw_window_expansion_never_calls_remote(self):
        class Forbidden:
            async def achat(self,*args,**kwargs):
                raise AssertionError('Summary generation was called')
        text=''.join(str(i%10) for i in range(120000))
        sampler=RawSampler(llm=Forbidden(),doc_content=text,verbose=False)
        sample=SampleWindow(start_idx=3000,end_idx=3500,content=text[3000:3500],score=9)
        await sampler._generate_summary([sample],'question')
        self.assertEqual(sampler.expanded[0]['start'],2250)
        self.assertEqual(sampler.expanded[0]['end'],4250)
        self.assertEqual(sampler.expanded[0]['text'],text[2250:4250])

    async def test_small_document_returns_exact_text_without_remote_call(self):
        text='Exact source text.\n' * 10
        sampler=RawSampler(llm=None,doc_content=text,verbose=False)
        result=await sampler.get_roi('question')
        self.assertEqual(result.snippets[0]['snippet'],text)
        self.assertEqual(result.snippets[0]['end'],len(text))

    def test_native_order_deduplicates_without_promoting_later_files(self):
        self.assertEqual(RetrievalOnly._merge_file_paths(['b','a','b'],[],['c','a']),['b','a','c'])


if __name__=='__main__':
    unittest.main()
