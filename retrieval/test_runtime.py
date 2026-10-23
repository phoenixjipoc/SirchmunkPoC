"""Offline safety and evidence-integrity checks; run inside the same container."""
import asyncio
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from runtime import CheckedChat, ModelMismatch, RetrievalOnly, phase_call


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

    def test_native_order_deduplicates_without_promoting_later_files(self):
        self.assertEqual(RetrievalOnly._merge_file_paths(['b','a','b'],[],['c','a']),['b','a','c'])

    def test_retrieval_logs_with_timestamps_can_be_saved(self):
        import json
        from datetime import datetime
        from basic_run import save
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'result.json'
            save(path,{'references':[{'rank':1,'file':'correct.pdf'}],
                       'keyword_logs':[{'timestamp':datetime(2026,10,23)}]})
            self.assertEqual(json.loads(path.read_text())['references'][0]['file'],'correct.pdf')


if __name__=='__main__':
    unittest.main()
