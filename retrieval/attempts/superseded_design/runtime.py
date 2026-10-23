"""Container-side extraction-only adapter and request identity checks."""
import asyncio
import contextvars
import hashlib
import json
import os
import random
import time
from pathlib import Path

from sirchmunk.llm.openai_chat import OpenAIChat
from sirchmunk.search import AgenticSearch
from sirchmunk.retrieve.text_retriever import GrepRetriever
from sirchmunk.learnings.evidence_processor import MonteCarloEvidenceSampling
from sirchmunk.utils import create_logger

PHASE = contextvars.ContextVar('phase', default='unspecified')
ALLOWED = {'preflight', 'keywords', 'directory', 'sampling', 'support_review'}


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
                self.check(response.model, 'raw_response')
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


class RawSampler(MonteCarloEvidenceSampling):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.expanded = []
        self.probes = []

    async def _evaluate_batch(self, samples, query):
        result = await super()._evaluate_batch(samples, query)
        self.probes.extend(dict(start=s.start_idx,end=s.end_idx,score=s.score,
                                source=s.source,round=s.round_num,reasoning=s.reasoning) for s in result)
        return result

    async def _generate_summary(self, top_samples, query):
        for sample in sorted(top_samples,key=lambda s:s.start_idx):
            center = (sample.start_idx+sample.end_idx)//2
            start, end = max(0,center-self.roi_window//2), min(self.doc_len,center+self.roi_window//2)
            self.expanded.append(dict(start=start,end=end,text=self.doc[start:end],score=sample.score,
                                      reason=sample.reasoning))
        return '\n'.join(s['text'] for s in self.expanded)


async def retrieve(query, top_k, seed, chat, root, output):
    random.seed(seed)
    started = time.time()
    chat.query_id = query['id']
    begin_calls = len(chat.records)
    record = dict(query_id=query['id'],question=query['question'],seed=seed,top_k=top_k,
                  status='running',references=[],keyword_files=[],directory_files=[],merged_files=[])
    trace = output / 'traces' / f"{query['id']}.jsonl"
    search = RetrievalOnly(chat, output / 'state' / query['id'])
    try:
        (keywords, keyword_list), scan = await asyncio.gather(
            phase_call('keywords',search._probe_keywords(query['question'])),
            search._probe_dir_scan(['/mnt/docs/S'],enable=True,max_files=500))
        chat.ensure_running()
        record['keywords'] = keywords
        append(trace,dict(phase='keywords',keywords=keywords))
        # Keep exactly the upstream random selection and capture which files were shown.
        scanner = search._dir_scanner
        original_prompt = scanner._build_rank_prompt
        def capture_prompt(*args,**kwargs):
            prompt = original_prompt(*args,**kwargs)
            append(trace,dict(phase='directory_input',prompt=prompt))
            return prompt
        scanner._build_rank_prompt = capture_prompt
        keyword_files, directory_files = await asyncio.gather(
            search._retrieve_by_keywords(keyword_list,['/mnt/docs/S'],max_depth=5),
            phase_call('directory',search._rank_dir_scan_candidates(query['question'],scan)))
        chat.ensure_running()
        merged = search._merge_file_paths(keyword_files,[],directory_files)
        record.update(keyword_files=keyword_files,directory_files=directory_files,merged_files=merged)
        append(trace,dict(phase='candidate_order',keyword_files=keyword_files,directory_files=directory_files,
                          merged_files=merged,selected=merged[:top_k]))
        async def extract(rank,file):
            filename = Path(file).name
            ref = dict(rank=rank,file=filename,original_path=file,status='running')
            try:
                text_file = root / 'parsed' / (filename+'.txt')
                text = text_file.read_text(encoding='utf-8')
                ref.update(parsed_sha256=sha(text),parsed_chars=len(text),
                           extraction_route='full_text' if len(text)<100000 else 'sampled')
                if not text.strip():
                    raise ValueError('Parser produced empty text')
                sampler = RawSampler(llm=chat,doc_content=text,verbose=False)
                result = await phase_call('sampling',sampler.get_roi(query['question'],keywords,
                                                                   confidence_threshold=8.0,top_k=5))
                chat.ensure_running()
                passages = sampler.expanded or [dict(start=s['start'],end=s['end'],text=s['snippet'],
                                                     score=s['score'],reason=s.get('reasoning',''))
                                                for s in result.snippets]
                for p in passages:
                    assert text[p['start']:p['end']] == p['text']
                ref.update(status='ok',sampler_is_found=result.is_found,passages=passages,probes=sampler.probes,
                           returned_chars=sum(len(p['text']) for p in passages))
            except ModelMismatch:
                raise
            except Exception as exc:
                ref.update(status='extraction_error',error=f'{type(exc).__name__}: {exc}')
            append(trace,dict(phase='raw_evidence',reference=ref))
            return ref
        record['references'] = await asyncio.gather(*(extract(i+1,f) for i,f in enumerate(merged[:top_k])))
        errors = [r for r in chat.records[begin_calls:] if r['status']=='error']
        record['status'] = 'call_error' if errors else ('ok' if merged else 'empty_retrieval')
    except ModelMismatch:
        record['status'] = 'model_mismatch'
        raise
    except Exception as exc:
        record.update(status='query_error',error=f'{type(exc).__name__}: {exc}')
    finally:
        record.update(elapsed_s=round(time.time()-started,3),calls=len(chat.records)-begin_calls,
                      token_usage={key:sum(r.get('usage',{}).get(key,0) or 0 for r in chat.records[begin_calls:])
                                   for key in ('prompt_tokens','completion_tokens','total_tokens')})
        (output / 'queries').mkdir(parents=True,exist_ok=True)
        (output / 'queries' / f"{query['id']}.json").write_text(json.dumps(record,ensure_ascii=False),encoding='utf-8')
    return record
