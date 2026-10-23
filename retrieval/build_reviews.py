"""Create blind support-check jobs for returned files outside verified source labels."""
import hashlib
import json
import re
from pathlib import Path

HERE=Path(__file__).resolve().parent
REPO=HERE.parent


def normalize(text):
    return re.sub(r'\s+',' ',text).strip()


def main():
    standards={s['id']:s for s in json.loads((HERE/'inputs/standards.json').read_text(encoding='utf-8'))}
    pack=HERE/'review_inputs'
    (pack/'texts').mkdir(parents=True,exist_ok=True)
    jobs=[]
    for p in sorted((HERE/'results/basic120/queries').glob('*.json')):
        result=json.loads(p.read_text(encoding='utf-8'))
        standard=standards[result['query_id']]
        if standard['scope']!='single_document':
            continue
        for ref in result['references']:
            if ref['file'] in standard['known_supporting_sources']:
                continue
            source=REPO/'poc/questions/verification/audit_20261014/source_text'/(ref['file']+'.txt')
            text=normalize(source.read_text(encoding='utf-8'))
            text_hash=hashlib.sha256(text.encode()).hexdigest()
            (pack/'texts'/(text_hash+'.txt')).write_text(text,encoding='utf-8')
            job=dict(id=hashlib.sha256((standard['id']+'|'+ref['file']).encode()).hexdigest()[:20],
                     query_id=standard['id'],question=standard['question'],file=ref['file'],
                     expected_facts=standard['gold_answer'],acceptance=standard['acceptance'],
                     text_hash=text_hash,source_text_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                     second_check_required=ref['rank']==1)
            jobs.append(job)
    (pack/'jobs.json').write_text(json.dumps(jobs,ensure_ascii=False,indent=2),encoding='utf-8')
    (pack/'manifest.json').write_text(json.dumps(dict(jobs=len(jobs),text_files=len({j['text_hash'] for j in jobs}),
                jobs_sha256=hashlib.sha256((pack/'jobs.json').read_bytes()).hexdigest()),indent=2))
    print(json.dumps({'unlisted_document_checks':len(jobs),'top1_checks':sum(j['second_check_required'] for j in jobs)}))


if __name__=='__main__':
    main()
