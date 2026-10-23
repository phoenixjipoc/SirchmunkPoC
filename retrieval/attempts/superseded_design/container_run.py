"""Freeze installed parsing and source code, then execute full repetitions."""
import argparse
import asyncio
import hashlib
import importlib.metadata
import inspect
import json
import os
import time
from pathlib import Path

from runtime import CheckedChat, ModelMismatch, append, phase_call, retrieve, sha


async def prepare(root):
    from sirchmunk.utils.file_utils import fast_extract
    from sirchmunk.search import AgenticSearch
    expected = json.loads((root/'inputs/corpus.json').read_text())
    actual = {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in Path('/mnt/docs/S').iterdir() if p.is_file()}
    assert actual == {x['file']:x['sha256'] for x in expected}, 'Corpus hash mismatch'
    (root/'parsed').mkdir(exist_ok=True)
    (root/'source_snapshot').mkdir(exist_ok=True)
    source_root = Path(inspect.getfile(AgenticSearch)).parent
    source_hashes = {}
    for relative in ['search.py','llm/openai_chat.py','llm/prompts.py','scan/dir_scanner.py',
                     'learnings/evidence_processor.py','retrieve/text_retriever.py','agentic/tools.py','utils/file_utils.py']:
        p=source_root/relative
        if p.is_file():
            source_hashes[relative]=hashlib.sha256(p.read_bytes()).hexdigest()
            target=root/'source_snapshot'/relative
            target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes(p.read_bytes())
    records=[]
    for item in expected:
        rec=dict(item)
        try:
            extracted=await asyncio.wait_for(fast_extract('/mnt/docs/S/'+item['file']),120)
            text=extracted.content or ''
            (root/'parsed'/(item['file']+'.txt')).write_text(text,encoding='utf-8')
            rec.update(chars=len(text),parsed_sha256=sha(text),status='ok' if text.strip() else 'empty',
                       control_characters=sum(ord(c)<32 and c not in '\n\r\t' for c in text))
        except Exception as exc:
            rec.update(status='error',error=f'{type(exc).__name__}: {exc}')
        records.append(rec)
        print(json.dumps({'prepared':len(records),'file':rec['file'],'status':rec['status']}),flush=True)
    config=json.loads((root/'inputs/config.json').read_text())
    chat=CheckedChat(config['model'],root/'preflight_calls.jsonl',root/'STOP_MODEL_MISMATCH')
    response=await phase_call('preflight',chat.achat([{'role':'user','content':'Reply with exactly OK.'}]))
    assert response.content.strip()=='OK', 'Unexpected preflight reply'
    await chat.close()
    data=dict(prepared_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
              version=importlib.metadata.version('sirchmunk'),source_hashes=source_hashes,
              files=records,model=config['model'],model_preflight_passed=True,
              code_hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in root.glob('*.py')})
    (root/'preflight.json').write_text(json.dumps(data,indent=2))


async def run(root,name):
    config=json.loads((root/'inputs/config.json').read_text())
    group,rep=name.split('_r')
    top_k=config['groups'][group]
    seed=config['seeds'][int(rep)-1]
    output=root/'runs'/name
    output.mkdir(parents=True,exist_ok=True)
    preflight=json.loads((root/'preflight.json').read_text())
    assert preflight['model_preflight_passed'] and preflight['model']==config['model']
    for filename,digest in preflight['code_hashes'].items():
        assert hashlib.sha256((root/filename).read_bytes()).hexdigest()==digest, 'Code changed after freeze'
    chat=CheckedChat(config['model'],output/'calls.jsonl',root/'STOP_MODEL_MISMATCH')
    queries=json.loads((root/'inputs/queries.json').read_text())
    started=time.time()
    complete=[]
    for index,q in enumerate(queries):
        target=output/'queries'/(q['id']+'.json')
        if target.exists():
            complete.append(json.loads(target.read_text()))
            continue
        query_seed=seed+int(sha(q['id'])[:8],16)
        try:
            result=await asyncio.wait_for(retrieve(q,top_k,query_seed,chat,root,output),config['query_timeout_s'])
        except ModelMismatch:
            raise
        except TimeoutError:
            result=json.loads(target.read_text()) if target.exists() else dict(query_id=q['id'],references=[])
            result['status']='timeout'
            target.write_text(json.dumps(result))
        complete.append(result)
        append(output/'progress.jsonl',dict(index=index+1,total=120,query_id=q['id'],status=result['status'],
                                           elapsed_s=result.get('elapsed_s'),references=len(result['references'])))
        print(f"{name} {index+1}/120 {q['id']} {result['status']} refs={len(result['references'])}",flush=True)
    await chat.close()
    (output/'complete.json').write_text(json.dumps(dict(run=name,questions=len(complete),
                        elapsed_s=round(time.time()-started,2),model=config['model'],
                        statuses={s:sum(r['status']==s for r in complete) for s in {r['status'] for r in complete}}),indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('action',choices=['prepare','run'])
    parser.add_argument('--root',type=Path,default=Path('/retrieval_20261023'))
    parser.add_argument('--name')
    args=parser.parse_args()
    asyncio.run(prepare(args.root) if args.action=='prepare' else run(args.root,args.name))
