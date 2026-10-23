"""Recover technical failures without rerunning any completed query or changing retrieval."""
import argparse
import asyncio
import hashlib
import json
import shutil
import time
from pathlib import Path

from basic_run import one,save
from runtime import CheckedChat,ModelMismatch,append


async def main(root):
    config=json.loads((root/'inputs/config.json').read_text())
    output=root/'results/basic120'
    preflight=json.loads((output/'preflight.json').read_text())
    for folder,records in [(root,preflight['code_hashes']),(root/'inputs',preflight['input_hashes'])]:
        for name,digest in records.items():
            assert hashlib.sha256((folder/name).read_bytes()).hexdigest()==digest,'Frozen code/input changed'
    previous=output/'complete.json'
    if previous.exists():
        previous.rename(output/'initial_attempt_complete.json')
    questions=json.loads((root/'inputs/queries.json').read_text())
    archive=output/'failed_attempts'
    archive.mkdir(exist_ok=True)
    chat=CheckedChat(config['model'],output/'calls_resume.jsonl',root/'STOP_MODEL_MISMATCH')
    recovered=[]; retained=[]; streak=0; started=time.time()
    for index,q in enumerate(questions):
        path=output/'queries'/(q['id']+'.json')
        original=json.loads(path.read_text()) if path.exists() else None
        if original and original['status'] in {'ok','empty_retrieval'}:
            retained.append(q['id']); continue
        if path.exists() and not (archive/path.name).exists(): shutil.copy2(path,archive/path.name)
        try:
            result=await asyncio.wait_for(one(q,root,chat,config),config['query_timeout_s'])
        except TimeoutError:
            result=json.loads(path.read_text())
        append(output/'recovery_progress.jsonl',dict(id=q['id'],index=index+1,status=result['status'],seconds=result['elapsed_s']))
        print(json.dumps({'recovery':q['id'],'index':index+1,'total':120,'status':result['status'],'seconds':result['elapsed_s']}),flush=True)
        if result['status'] in {'ok','empty_retrieval'}:
            recovered.append(q['id']); streak=0
        else:
            streak+=1
            if streak>=3:
                await chat.close()
                raise RuntimeError('Three consecutive technical failures; recovery stopped')
    await chat.close()
    final=[json.loads((output/'queries'/(q['id']+'.json')).read_text()) for q in questions]
    save(output/'complete.json',dict(questions=len(final),
        statuses={s:sum(r['status']==s for r in final) for s in {r['status'] for r in final}},
        recovery_elapsed_s=round(time.time()-started,3),retained_query_ids=retained,recovered_query_ids=recovered,
        recovery_script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()))


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--root',type=Path,default=Path('/retrieval_basic_20261023_v2'))
    asyncio.run(main(parser.parse_args().root))
