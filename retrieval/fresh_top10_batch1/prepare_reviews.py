"""Reuse compatible source checks and upgrade newly first-ranked exceptions."""
import hashlib
import re
import shutil
from common import HERE, read, save, sha

def norm(text):
    return re.sub(r'\s+', ' ', text).strip()

def main():
    assert (HERE/'retrieval_complete.json').exists()
    parent = HERE.parent
    standards_path = parent/'inputs/standards.json'
    import subprocess
    committed = subprocess.check_output(['git','show',read(HERE/'freeze.json')['source_commit']+':retrieval/inputs/standards.json'],cwd=parent.parent)
    assert hashlib.sha256(committed).hexdigest()==sha(standards_path), 'Scoring standards changed since batch preparation'
    standards = {s['id']: s for s in read(standards_path)}
    (HERE/'scoring_inputs').mkdir(exist_ok=True)
    shutil.copyfile(standards_path, HERE/'scoring_inputs/standards.json')
    checked = {}; adjudicated = {}; dependencies = {str(standards_path.relative_to(parent.parent)): sha(standards_path)}
    for folder in [parent/'support_reviews', parent/'followup120/support_reviews', parent/'rerank_top5_top10/support_reviews']:
        for p in sorted(folder.glob('*.json')):
            r = read(p)
            if 'job' in r:
                key = (r['job']['query_id'], r['job']['file'])
                checked[key] = (r, p)
        p = folder/'adjudications.jsonl'
        if p.exists():
            for line in p.read_text(encoding='utf-8').splitlines():
                import json
                r = json.loads(line)
                adjudicated[r['query_id'],r['file']] = (r,p)
    pool = {}
    for group in ['Baseline','RR10']:
        folder = HERE/'baseline' if group=='Baseline' else HERE/'runs'/group/'queries'
        assert {p.stem for p in folder.glob('*.json')}==set(standards), f'Incomplete collection: {group}'
        for p in sorted(folder.glob('*.json')):
            r = read(p); qid = r['query_id']; s = standards[qid]
            if s['scope'] != 'single_document':
                continue
            for ref in r['references']:
                if ref['file'] in s['known_supporting_sources']:
                    continue
                item = pool.setdefault((qid,ref['file']),dict(first=False,positions=[]))
                item['first'] |= ref['rank']==1
                item['positions'].append(dict(group=group,rank=ref['rank']))
    audit = parent.parent/'poc/questions/verification/audit_20261014/source_text'
    reused = []; jobs = []
    for (qid,name), flags in sorted(pool.items()):
        s = standards[qid]
        source = audit/(name+'.txt')
        text = norm(source.read_text(encoding='utf-8-sig'))
        thash = hashlib.sha256(text.encode()).hexdigest()
        prior, path = checked.get((qid,name),(None,None))
        if prior:
            job = prior['job']
            assert job['question']==s['question'] and job['acceptance']==s['acceptance']
            assert job['expected_facts']==s['gold_answer'] and job['text_hash']==thash
        adj, adjpath = adjudicated.get((qid,name),(None,None))
        ready = prior and prior.get('support') is not None and all(v.get('coverage') in {'full','partial','none'} for v in prior['reviews'])
        enough = prior and (not flags['first'] or len(prior['reviews'])>=2)
        if adj or (ready and enough):
            used = adjpath if adj else path
            dependencies[used.relative_to(parent.parent).as_posix()] = sha(used)
            reused.append(dict(query_id=qid,file=name,support=adj['support'] if adj else prior['support'],
                source_path=used.relative_to(parent.parent).as_posix(), source_sha256=sha(used), text_hash=thash,
                first_position=flags['first'], review_count=len(prior['reviews']) if prior else 0,
                adjudicated=bool(adj)))
            continue
        jid = hashlib.sha256((qid+'|'+name).encode()).hexdigest()[:20]
        job = dict(id=jid, query_id=qid, question=s['question'], file=name, expected_facts=s['gold_answer'],
            acceptance=s['acceptance'], text_hash=thash, source_text_sha256=sha(source),
            second_check_required=flags['first'], prior_reviews=prior['reviews'] if ready else [])
        if ready:
            dependencies[path.relative_to(parent.parent).as_posix()] = sha(path)
            job['prior_source_path']=path.relative_to(parent.parent).as_posix()
            job['prior_source_sha256']=sha(path)
        save(HERE/'review_inputs/jobs'/(jid+'.json'),job)
        textpath=HERE/'review_inputs/texts'/(thash+'.txt')
        textpath.parent.mkdir(parents=True,exist_ok=True)
        textpath.write_text(text,encoding='utf-8')
        jobs.append(job)
    save(HERE/'scoring_inputs/reused_support.json',reused)
    save(HERE/'scoring_inputs/pooled_references.json',[dict(query_id=k[0],file=k[1],**v) for k,v in sorted(pool.items())])
    save(HERE/'review_inputs/jobs.json',jobs)
    save(HERE/'review_inputs/manifest.json',dict(associations=len(pool),reused=len(reused),jobs=len(jobs),
        upgrades=sum(bool(j['prior_reviews']) for j in jobs)))
    local=list((HERE/'scoring_inputs').glob('*.json'))+list((HERE/'review_inputs').rglob('*'))
    save(HERE/'scoring_freeze.json',dict(dependencies=dependencies,
        files={p.relative_to(HERE).as_posix():sha(p) for p in local if p.is_file()}))
    print(read(HERE/'review_inputs/manifest.json'))

if __name__=='__main__':
    main()
