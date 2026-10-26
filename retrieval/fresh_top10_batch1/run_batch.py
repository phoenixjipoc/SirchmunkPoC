"""Fresh native retrieval, then a single paired reranking pass."""
import argparse
import asyncio
import hashlib
import inspect
import json
import shutil
import sys
import time
from collections import Counter
from pathlib import Path
from common import read,save,sha

sys.path.insert(0,str(Path(__file__).parent/'adapter'))
from basic_run import prepare as fresh_prepare,one as retrieve
from runtime import CheckedChat,ModelMismatch,append
from rank_adapter import preflight,one as rerank

def verify(root):
    frozen=dict(read(root/'freeze.json')['files'])
    if (root/'execution_repair/revision.json').exists():
        revision=read(root/'execution_repair/revision.json')
        for name,item in revision['changes'].items():
            assert frozen[name]==item['before_sha256']
            assert sha(root/item['original_copy'])==item['before_sha256']
            frozen[name]=item['after_sha256']
    for name,expected in frozen.items():
        assert sha(root/name)==expected, f'Frozen input changed: {name}'
    actual={p.name:sha(p) for p in Path('/mnt/docs/S').iterdir() if p.is_file()}
    assert actual=={r['file']:r['sha256'] for r in read(root/'inputs/corpus.json')}
    import sirchmunk
    installed=Path(inspect.getfile(sirchmunk)).parent
    for name,expected in read(root/'inputs/source_hashes.json').items():
        assert sha(installed/name)==expected, f'Installed source changed: {name}'

def completed(row):
    return row['status'] in {'ok','empty_retrieval','technical_failure'}

async def retrieval_stage(root,settings,config,queries):
    output=root/'runs/Baseline'
    chat=CheckedChat(settings['model'],output/'calls.jsonl',root/'STOP_MODEL_MISMATCH')
    try:
        for i,q in enumerate(queries):
            dest=output/'queries'/(q['id']+'.json')
            if dest.exists() and completed(read(dest)): continue
            folder=output/'attempts'/q['id']
            prior=sorted(folder.glob('*.json'))
            result=read(prior[-1]) if prior else None
            if not (result and result['status'] in {'ok','empty_retrieval'}):
                for attempt in range(len(prior)+1,4):
                    before=len(chat.records)
                    chat.query_id=q['id']
                    try:
                        result=await asyncio.wait_for(retrieve(q,root,chat,config),config['query_timeout_s'])
                    except ModelMismatch: raise
                    except TimeoutError:
                        result=read(root/'results/basic120/queries'/(q['id']+'.json'))
                    result.update(group='Baseline',attempt=attempt,executed_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()))
                    save(folder/f'{attempt}.json',result)
                    new=chat.records[before:]
                    fatal=[c for c in new if c.get('error_type') in {'AuthenticationError','PermissionDeniedError','NotFoundError'} or 'insufficient_quota' in c.get('error','')]
                    if fatal: raise RuntimeError('Service authorization/configuration error; inspect call records')
                    if result['status'] in {'ok','empty_retrieval'}: break
                    # Do not consume more query attempts while the service is unavailable.
                    await preflight(root,settings)
                    if attempt<3: await asyncio.sleep(5)
            if result is None: raise RuntimeError('Missing retrieval attempt')
            attempts=[read(p) for p in folder.glob('*.json')]
            if result['status'] not in {'ok','empty_retrieval'}:
                result={**result,'status':'technical_failure','references':[]}
            result['attempts']=len(attempts)
            result['total_attempt_seconds']=sum(a['elapsed_s'] for a in attempts)
            save(dest,result)
            append(root/'progress.jsonl',dict(group='Baseline',index=i+1,id=q['id'],status=result['status']))
            print(json.dumps(dict(group='Baseline',index=i+1,total=120,id=q['id'],status=result['status'],references=len(result['references']))),flush=True)
    finally: await chat.close()
    rows=[read(p) for p in (output/'queries').glob('*.json')]
    assert {r['query_id'] for r in rows}=={q['id'] for q in queries}
    save(output/'complete.json',dict(questions=len(rows),statuses=dict(Counter(r['status'] for r in rows))))
    save(root/'fresh_retrieval_complete.json',dict(questions=len(rows),finished_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())))

def prepare_reranking(root,settings,queries):
    if (root/'rerank_freeze.json').exists():
        for name,expected in read(root/'rerank_freeze.json')['files'].items(): assert sha(root/name)==expected
        return
    scan={c['filename']:c for c in read(root/'inputs/directory_scan.json')['candidates']}
    ids={name:f'd{i:03d}' for i,name in enumerate(sorted(scan),1)}
    save(root/'inputs/document_ids.json',ids)
    for q in queries:
        src=root/'runs/Baseline/queries'/(q['id']+'.json')
        target=root/'baseline'/src.name
        target.parent.mkdir(exist_ok=True)
        shutil.copyfile(src,target)
        result=read(src);files=[r['file'] for r in result['references']]
        order=sorted(files,key=lambda name:hashlib.sha256(f"{settings['presentation_seed']}|{q['id']}|{name}".encode()).hexdigest())
        payload=dict(question=q['question'],documents=[dict(id=ids[name],file=name,title=scan[name].get('title') or '',
            keywords=scan[name].get('keywords') or [],preview=(scan[name].get('preview') or '')[:800]) for name in order])
        save(root/'inputs/payloads/RR10'/(q['id']+'.json'),payload)
    files=[*list((root/'baseline').glob('*.json')),*list((root/'inputs/payloads/RR10').glob('*.json')),
        root/'inputs/document_ids.json',root/'inputs/directory_scan.json',*list((root/'runs/Baseline').rglob('*.json')),
        root/'runs/Baseline/calls.jsonl']
    save(root/'rerank_freeze.json',dict(files={p.relative_to(root).as_posix():sha(p) for p in sorted(files)},
        source='Fresh Baseline from this batch; no historical candidate lists'))

async def main(root):
    verify(root)
    settings=read(root/'settings.json'); config=read(root/'inputs/config.json');queries=read(root/'inputs/queries.json')
    assert len(queries)==120
    if not (root/'scan_freeze.json').exists():
        await fresh_prepare(root)
        save(root/'scan_freeze.json',dict(files={n:sha(root/n) for n in ['inputs/directory_scan.json','results/basic120/preflight.json']},
            fresh_cache=True,fresh_directory_scan=True))
    for name,expected in read(root/'scan_freeze.json')['files'].items(): assert sha(root/name)==expected
    await preflight(root,settings)
    if not (root/'fresh_retrieval_complete.json').exists():
        await retrieval_stage(root,settings,config,queries)
    prepare_reranking(root,settings,queries)
    chat=CheckedChat(settings['model'],root/'runs/RR10/calls.jsonl',root/'STOP_MODEL_MISMATCH',concurrency=1)
    try:
        for q in queries: await rerank(root,q,'RR10',settings,chat)
    finally: await chat.close()
    rows=[read(p) for p in (root/'runs/RR10/queries').glob('*.json')]
    assert {r['query_id'] for r in rows}=={q['id'] for q in queries}
    save(root/'runs/RR10/complete.json',dict(questions=len(rows),statuses=dict(Counter(r['status'] for r in rows))))
    save(root/'retrieval_complete.json',dict(groups=['Baseline','RR10'],tasks=240,repetitions=1,
        finished_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=Path(__file__).parent)
    args=p.parse_args();asyncio.run(main(args.root))
