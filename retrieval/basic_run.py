"""Run one full document retrieval benchmark; no evidence or answer generation."""
import argparse
import asyncio
import dataclasses
import hashlib
import inspect
import json
import random
import subprocess
import time
from pathlib import Path

from runtime import CheckedChat, RetrievalOnly, ModelMismatch, append, phase_call, sha
from sirchmunk.scan.dir_scanner import DirectoryScanner, FileCandidate, ScanResult
from sirchmunk.agentic.tools import KeywordSearchTool
from sirchmunk.schema.search_context import SearchContext


def save(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2,default=str),encoding='utf-8')


async def prepare(root):
    expected=json.loads((root/'inputs/corpus.json').read_text())
    actual={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in Path('/mnt/docs/S').iterdir() if p.is_file()}
    assert actual=={x['file']:x['sha256'] for x in expected},'Corpus changed'
    config=json.loads((root/'inputs/config.json').read_text())
    (root/'cache/rga').mkdir(parents=True,exist_ok=True)
    records=[]
    started=time.time()
    for item in expected:
        try:
            p=await asyncio.create_subprocess_exec('rga','--no-config','--rga-cache-max-blob-len=10000000',
                    f'--rga-cache-path={root}/cache/rga','-m','1','[A-Za-z]','/mnt/docs/S/'+item['file'],
                    stdout=asyncio.subprocess.PIPE,stderr=asyncio.subprocess.PIPE)
            stdout,stderr=await asyncio.wait_for(p.communicate(),60)
            records.append(dict(file=item['file'],returncode=p.returncode,has_text=bool(stdout.strip()),
                                stderr=stderr.decode(errors='replace')[:1500]))
        except TimeoutError:
            p.kill(); await p.communicate()
            records.append(dict(file=item['file'],status='timeout'))
    scanner=DirectoryScanner(llm=None,max_files=500)
    scan=await scanner.scan(['/mnt/docs/S'])
    save(root/'inputs/directory_scan.json',dataclasses.asdict(scan))
    chat=CheckedChat(config['model'],root/'results/basic120/preflight_calls.jsonl',root/'STOP_MODEL_MISMATCH')
    result=await phase_call('preflight',chat.achat([{'role':'user','content':'Reply with exactly OK.'}]))
    assert result.content.strip()=='OK'
    await chat.close()
    # Freeze every installed source file used by this adapter's package.
    import sirchmunk
    source_root=Path(inspect.getfile(sirchmunk)).parent
    sources={str(p.relative_to(source_root)):hashlib.sha256(p.read_bytes()).hexdigest()
             for p in source_root.rglob('*.py')}
    code={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in root.glob('*.py')}
    inputs={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (root/'inputs').glob('*.json')}
    save(root/'results/basic120/preflight.json',dict(model=config['model'],model_preflight_passed=True,
        corpus_hashes_match=True,scan_files=scan.total_files,rga=records,source_hashes=sources,
        code_hashes=code,input_hashes=inputs,warmup_s=round(time.time()-started,3),
        directory_snapshot_sha256=hashlib.sha256((root/'inputs/directory_scan.json').read_bytes()).hexdigest()))
    print(json.dumps({'prepared':True,'files':scan.total_files,'rga_text':sum(r.get('has_text',False) for r in records)}),flush=True)


class DocumentSearch(RetrievalOnly):
    def __init__(self,chat,root):
        super().__init__(chat,root/'state')
        self.grep_retriever.rga_cache=root/'cache/rga'
        self._dir_scanner=DirectoryScanner(llm=chat,max_files=500)
        self.keyword_logs=[]

    async def keywords(self,terms):
        # Same tool, options and log-derived order as _retrieve_by_keywords;
        # preserve its context logs as additional observability.
        tool=KeywordSearchTool(retriever=self.grep_retriever,paths=['/mnt/docs/S'],max_depth=5,max_results=20)
        ctx=SearchContext()
        result,meta=await tool.execute(context=ctx,keywords=terms)
        found=[]
        for entry in ctx.retrieval_logs:
            found.extend(entry.metadata.get('files_discovered',[]))
            self.keyword_logs.append(entry.model_dump(mode='json') if hasattr(entry,'model_dump') else vars(entry))
        return found


async def one(q,root,chat,config):
    start=time.time()
    seed=config['seeds'][0]+int(sha(q['id'])[:8],16)
    random.seed(seed)
    chat.query_id=q['id']
    call_start=len(chat.records)
    record=dict(query_id=q['id'],question=q['question'],type=q['type'],pair_id=q['pair_id'],seed=seed,
                references=[],status='running',evidence_sampling=False,answer_generated=False,cluster_used=False)
    output=root/'results/basic120'
    search=DocumentSearch(chat,root)
    raw=json.loads((root/'inputs/directory_scan.json').read_text())
    scan=ScanResult(candidates=[FileCandidate(**c) for c in raw['candidates']],
                    total_files=raw['total_files'],total_dirs=raw['total_dirs'])
    original_prompt=search._dir_scanner._build_rank_prompt
    def capture(*args,**kwargs):
        prompt=original_prompt(*args,**kwargs)
        record['directory_prompt']=prompt
        return prompt
    search._dir_scanner._build_rank_prompt=capture
    try:
        keywords,terms=await phase_call('keywords',search._probe_keywords(q['question']))
        chat.ensure_running()
        record.update(keywords=keywords,keyword_terms=terms)
        kw,dirs=await asyncio.gather(search.keywords(terms),
                phase_call('directory',search._rank_dir_scan_candidates(q['question'],scan)))
        chat.ensure_running()
        merged=search._merge_file_paths(kw,[],dirs)
        record.update(keyword_files=kw,directory_files=dirs,merged_files=merged,
            references=[dict(rank=i+1,file=Path(p).name,path=p) for i,p in enumerate(merged[:10])],
            directory_ranking=[c.to_dict() for c in scan.ranked_candidates],keyword_logs=search.keyword_logs)
        bad=[c for c in chat.records[call_start:] if c['status']!='ok' or c.get('finish_reason')!='stop']
        record['status']='call_error' if bad else ('ok' if merged else 'empty_retrieval')
    except ModelMismatch:
        record['status']='model_mismatch'
        raise
    except asyncio.CancelledError:
        record['status']='timeout'
        raise
    except Exception as exc:
        record.update(status='query_error',error=f'{type(exc).__name__}: {exc}')
    finally:
        record.update(elapsed_s=round(time.time()-start,3),calls=len(chat.records)-call_start,
                      usage={k:sum(c.get('usage',{}).get(k,0) or 0 for c in chat.records[call_start:])
                             for k in ['prompt_tokens','completion_tokens','total_tokens']})
        save(output/'queries'/f"{q['id']}.json",record)
    return record


async def run(root):
    config=json.loads((root/'inputs/config.json').read_text())
    preflight=json.loads((root/'results/basic120/preflight.json').read_text())
    for folder,records in [(root,preflight['code_hashes']),(root/'inputs',preflight['input_hashes'])]:
        for name,digest in records.items():
            assert hashlib.sha256((folder/name).read_bytes()).hexdigest()==digest,'Frozen input/code changed'
    output=root/'results/basic120'
    chat=CheckedChat(config['model'],output/'calls.jsonl',root/'STOP_MODEL_MISMATCH')
    queries=json.loads((root/'inputs/queries.json').read_text())
    results=[]
    started=time.time()
    for i,q in enumerate(queries):
        path=output/'queries'/f"{q['id']}.json"
        if path.exists():
            results.append(json.loads(path.read_text())); continue
        try:
            r=await asyncio.wait_for(one(q,root,chat,config),config['query_timeout_s'])
        except TimeoutError:
            r=json.loads(path.read_text())
        results.append(r)
        progress=dict(index=i+1,total=len(queries),id=q['id'],status=r['status'],seconds=r['elapsed_s'],references=len(r['references']))
        append(output/'progress.jsonl',progress)
        print(json.dumps(progress),flush=True)
    await chat.close()
    save(output/'complete.json',dict(questions=len(results),elapsed_s=round(time.time()-started,3),
              statuses={s:sum(r['status']==s for r in results) for s in {r['status'] for r in results}}))


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('action',choices=['prepare','run'])
    parser.add_argument('--root',type=Path,default=Path('/retrieval_basic_20261023'))
    args=parser.parse_args()
    asyncio.run(prepare(args.root) if args.action=='prepare' else run(args.root))
