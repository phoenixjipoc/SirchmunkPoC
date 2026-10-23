"""Review completed retrieval outputs in a separate, read-only assessment process."""
import argparse
import asyncio
import hashlib
import json
from pathlib import Path

from review_support import main as review_jobs


async def main(root,results,model):
    pack=root/'review_inputs'
    standards={s['id']:s for s in json.loads((pack/'standards.json').read_text())}
    texts=json.loads((pack/'text_manifest.json').read_text())
    while True:
        jobs=[]; parsed=0
        for p in sorted((results/'queries').glob('*.json')):
            try:
                result=json.loads(p.read_text())
            except json.JSONDecodeError:
                continue
            parsed+=1
            s=standards[result['query_id']]
            if s['scope']!='single_document': continue
            for ref in result['references']:
                if ref['file'] in s['known_supporting_sources']: continue
                info=texts[ref['file']]
                jobs.append(dict(id=hashlib.sha256((s['id']+'|'+ref['file']).encode()).hexdigest()[:20],
                    query_id=s['id'],question=s['question'],file=ref['file'],expected_facts=s['gold_answer'],
                    acceptance=s['acceptance'],text_hash=info['text_hash'],source_text_sha256=info['source_text_sha256'],
                    second_check_required=ref['rank']==1))
        (pack/'jobs.json').write_text(json.dumps(jobs,ensure_ascii=False,indent=2),encoding='utf-8')
        await review_jobs(root,model)
        if (results/'complete.json').exists() and parsed==120:
            (root/'support_complete.json').write_text(json.dumps({'queries':parsed,'document_checks':len(jobs)}))
            print('All support checks complete.',flush=True)
            return
        await asyncio.sleep(20)


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--root',type=Path,default=Path('/retrieval_support_20261023'))
    parser.add_argument('--results',type=Path,default=Path('/retrieval_basic_20261023_v2/results/basic120'))
    parser.add_argument('--model',default='gpt-6-sol')
    args=parser.parse_args()
    asyncio.run(main(args.root,args.results,args.model))
