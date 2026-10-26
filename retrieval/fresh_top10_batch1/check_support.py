"""Run separate source checks after timed retrieval; cached checks are immutable."""
import argparse
import asyncio
import json
import sys
import time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent/'adapter'))
from runtime import CheckedChat,ModelMismatch,phase_call,sha
from review_support import SYSTEM_A,SYSTEM_B,validate


async def main(root,workers=4):
    assert (root/'retrieval_complete.json').exists(), 'Do not run scoring concurrently with retrieval'
    jobs=json.loads((root/'review_inputs/jobs.json').read_text())
    output=root/'support_reviews'; output.mkdir(exist_ok=True)
    queue=asyncio.Queue()
    for job in jobs:
        if not (output/(job['id']+'.json')).exists(): queue.put_nowait(job)
    started=time.time()
    async def worker(number):
        chat=CheckedChat('gpt-6-sol',output/f'calls_{number}.jsonl',root/'STOP_MODEL_MISMATCH',concurrency=1)
        try:
            while not queue.empty():
                job=queue.get_nowait()
                text=(root/'review_inputs/texts'/(job['text_hash']+'.txt')).read_text(encoding='utf-8')
                assert sha(text)==job['text_hash']
                record=dict(job=job,reviews=list(job['prior_reviews']),support=None)
                pending=output/'pending'/(job['id']+'.json')
                if pending.exists(): record=json.loads(pending.read_text(encoding='utf-8'))
                last_error=None
                prompt=json.dumps({k:job[k] for k in ['question','file','expected_facts','acceptance']},ensure_ascii=False)+'\nDOCUMENT:\n'+text
                for index,system in enumerate([SYSTEM_A,SYSTEM_B]):
                    if index<len(record['reviews']): continue
                    if index==1 and not (job['second_check_required'] or record['reviews'][0].get('coverage') in {'full','uncertain'}): break
                    chat.query_id=job['id']+':'+str(index+1)
                    verdict=None
                    for attempt in range(1,4):
                        try:
                            response=await phase_call('support_review',chat.achat(
                                [{'role':'system','content':system},{'role':'user','content':prompt}],
                                response_format={'type':'json_object'},max_completion_tokens=5000))
                            if chat.records[-1].get('finish_reason')!='stop': raise ValueError('Incomplete response')
                            verdict=validate(json.loads(response.content),text)
                            verdict.update(reviewer='AB'[index],attempt=attempt)
                            last_error=None
                            break
                        except ModelMismatch: raise
                        except Exception as exc:
                            last_error=exc
                            verdict=dict(reviewer='AB'[index],coverage='uncertain',attempt=attempt,error=f'{type(exc).__name__}: {exc}')
                            await asyncio.sleep(3)
                    record['reviews'].append(verdict)
                    pending.parent.mkdir(exist_ok=True)
                    pending.write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
                votes=[r['coverage'] for r in record['reviews']]
                if votes==['full','full']: record['support']=True
                elif all(v in {'none','partial'} for v in votes): record['support']=False
                (output/(job['id']+'.json')).write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
                print(json.dumps(dict(job=job['id'],query=job['query_id'],support=record['support'],remaining=queue.qsize())),flush=True)
                queue.task_done()
                if last_error is not None:
                    raise last_error
        finally: await chat.close()
    await asyncio.gather(*(worker(n) for n in range(1,workers+1)))
    (root/'support_complete.json').write_text(json.dumps(dict(jobs=len(jobs),workers=workers,elapsed_s=round(time.time()-started,3))))


if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--root',type=Path,default=Path('/retrieval_followup_20261023'))
    p.add_argument('--workers',type=int,choices=range(1,5),default=4)
    args=p.parse_args()
    asyncio.run(main(args.root,args.workers))
