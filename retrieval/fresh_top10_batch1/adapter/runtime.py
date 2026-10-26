"""Container-side document retrieval adapter and request identity checks."""
import asyncio
import contextvars
import hashlib
import json
import os
import time
from pathlib import Path

from sirchmunk.llm.openai_chat import OpenAIChat
from sirchmunk.search import AgenticSearch
from sirchmunk.retrieve.text_retriever import GrepRetriever
from sirchmunk.utils import create_logger

PHASE = contextvars.ContextVar('phase', default='unspecified')
WIRE = contextvars.ContextVar('wire', default=None)
ALLOWED = {'preflight', 'keywords', 'directory', 'support_review'}


def sha(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def append(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a', encoding='utf-8') as f:
        f.write(json.dumps(value, ensure_ascii=False, default=str) + '\n')


class ModelMismatch(RuntimeError):
    pass


class CheckedChat(OpenAIChat):
    def __init__(self, model, output, stop_file, concurrency=3):
        super().__init__(model=model, api_key=os.environ['LLM_API_KEY'],
                         base_url=os.environ.get('LLM_BASE_URL','https://api.openai.com/v1'),
                         max_retries=0)
        self.expected = model
        self.output = Path(output)
        self.stop_file = Path(stop_file)
        self.semaphore = asyncio.Semaphore(concurrency)
        self.records = []
        self.query_id = 'preflight'
        self._async_client.max_retries = 0
        self._async_client.timeout = 120.0
        original = self._async_client.chat.completions.create

        async def check_http(request):
            if request.url.path.endswith('/chat/completions'):
                body = json.loads(request.content)
                self.check(body.get('model'), 'outbound_http_body')
                if WIRE.get() is not None:
                    WIRE.get().append(body.get('model'))
        self._async_client._client.event_hooks['request'].append(check_http)

        async def checked_create(**kwargs):
            self.ensure_running()
            self.check(kwargs.get('model'), 'request_argument')
            if kwargs.get('stream'):
                raise RuntimeError('Only inspectable non-streaming responses are permitted')
            phase = PHASE.get()
            if phase not in ALLOWED:
                raise RuntimeError(f'Unexpected remote-call phase: {phase}')
            started = time.time()
            wire_token = WIRE.set([])
            rec = dict(query_id=self.query_id, phase=phase, requested_model=kwargs['model'],
                       prompt_sha256=sha(json.dumps(kwargs.get('messages'),sort_keys=True)),
                       started_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
                       prompt_chars=sum(len(str(m.get('content',''))) for m in kwargs.get('messages',[])))
            try:
                async with self.semaphore:
                    self.ensure_running()
                    response = await original(**kwargs)
                rec.update(response_model=response.model, response_id=response.id,
                           request_id=getattr(response,'_request_id',None),
                           usage=response.usage.model_dump() if response.usage else {},
                           finish_reason=response.choices[0].finish_reason if response.choices else None)
                rec['outbound_http_models'] = list(WIRE.get())
                rec['response_text'] = response.choices[0].message.content if response.choices else None
                self.check(response.model, 'raw_response')
                if not WIRE.get():
                    raise RuntimeError('No outbound HTTP model observation')
                rec['model_match'] = True
                rec['status'] = 'ok'
                return response
            except Exception as exc:
                rec.update(status='error',error_type=type(exc).__name__,error=str(exc)[:1500])
                raise
            finally:
                rec['elapsed_s'] = round(time.time()-started,3)
                self.records.append(rec)
                append(self.output,rec)
                WIRE.reset(wire_token)
        self._async_client.chat.completions.create = checked_create

    def check(self, actual, location):
        if actual != self.expected:
            self.stop_file.write_text(json.dumps({'expected':self.expected,'actual':actual,'location':location}))
            raise ModelMismatch(f'Model mismatch at {location}: {actual!r}')

    def ensure_running(self):
        if self.stop_file.exists():
            raise ModelMismatch('Campaign stopped by shared model guard')

    async def achat(self, messages, stream=False, **kwargs):
        self.ensure_running()
        result = await super().achat(messages=messages, stream=False, **kwargs)
        self.ensure_running()
        return result

    async def close(self):
        await self._async_client.close()
        self._client.close()


async def phase_call(name, awaitable):
    token = PHASE.set(name)
    try:
        return await awaitable
    finally:
        PHASE.reset(token)


class RetrievalOnly(AgenticSearch):
    """Initialize only dependencies of the inherited retrieval methods."""
    def __init__(self, chat, work_path):
        self.llm = chat
        self.work_path = Path(work_path)
        self.grep_retriever = GrepRetriever(work_path=self.work_path)
        self._logger = create_logger(enable_async=True)
        self._dir_scanner = None
        self.llm_usages = []
