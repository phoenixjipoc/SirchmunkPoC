"""Pool new references, reuse source-grounded checks, and freeze source anchors."""
import hashlib
import json
import re
from pathlib import Path

HERE=Path(__file__).resolve().parent
BASE=HERE.parent
AUDIT=BASE.parent/'poc/questions/verification/audit_20261014'


def read(p): return json.loads(p.read_text(encoding='utf-8'))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf-8')
def norm(t): return re.sub(r'\s+',' ',t).strip()


def results():
    groups={'R1':{p.stem:read(p) for p in (HERE/'baseline').glob('*.json')}}
    for group in ['R2','R3','D','P','P0']:
        folder=HERE/'runs'/group/'queries'
        if folder.exists(): groups[group]={p.stem:read(p) for p in folder.glob('*.json')}
    for group,key in [('K','keyword_files'),('T','directory_files')]:
        groups[group]={}
        for qid,old in groups['R1'].items():
            paths=list(dict.fromkeys(old[key]))
            r={**old,'group':group,'status':'ok' if paths else 'empty_retrieval',
               'references':[dict(rank=i+1,file=Path(p).name,path=p) for i,p in enumerate(paths[:10])],
               'merged_files':paths,'elapsed_s':0,'usage':{},'calls':0}
            groups[group][qid]=r
    return groups


def anchors(standards):
    evidence={}
    for p in AUDIT.glob('blind_answers_*.jsonl'):
        for line in p.read_text(encoding='utf-8-sig').splitlines():
            row=json.loads(line); evidence[row['id']]=row.get('evidence',[])
    hashes={r['file']:r['sha256'] for r in read(BASE/'inputs/corpus.json')}
    records=[]
    for s in standards.values():
        sources=[]
        for name in s['known_supporting_sources']:
            p=AUDIT/'source_text'/(name+'.txt')
            text=norm(p.read_text(encoding='utf-8-sig'))
            passages=[]
            for e in evidence.get(s['id'],[]):
                if e.get('file')!=name: continue
                quote=e.get('quote',e.get('text',''))
                passages.append({**e,'normalized_quote_found':bool(quote) and norm(quote) in text,
                                 'normalized_offset':text.find(norm(quote)) if quote else -1})
            sources.append(dict(file=name,original_sha256=hashes[name],source_text_sha256=sha(p),
                                anchors=passages))
        records.append(dict(id=s['id'],question=s['question'],scope=s['scope'],
                            expected_facts=s['gold_answer'],acceptance=s['acceptance'],
                            verified_passage=s['gold_passage'],source_audit_note=s['source_audit_note'],sources=sources))
    save(HERE/'scoring_inputs/standards_with_anchors.json',records)
    save(HERE/'scoring_inputs/anchor_validation.json',dict(questions=len(records),
         source_associations=sum(len(r['sources']) for r in records),
         quoted_anchors=sum(len(s['anchors']) for r in records for s in r['sources']),
         matched_anchors=sum(a['normalized_quote_found'] for r in records for s in r['sources'] for a in s['anchors']),
         interpretation='Original audit locators preserved; normalized substring matches validate text, not pagination. Summarized or discontinuous quotations can require the existing source audit.'))


def main():
    standards={r['id']:r for r in read(BASE/'inputs/standards.json')}
    anchors(standards)
    old_reviews={}
    for p in (BASE/'support_reviews').glob('*.json'):
        r=read(p)
        if 'job' in r: old_reviews[(r['job']['query_id'],r['job']['file'])]=r
    adjudicated={}
    for line in (BASE/'support_reviews/adjudications.jsonl').read_text(encoding='utf-8').splitlines():
        r=json.loads(line); adjudicated[(r['query_id'],r['file'])]=r
    pool={}
    groups=results()
    for group,rows in groups.items():
        assert len(rows)==120, f'Incomplete group: {group}'
        for qid,r in rows.items():
            s=standards[qid]
            if s['scope']!='single_document': continue
            for ref in r['references']:
                if ref['file'] in s['known_supporting_sources']: continue
                key=(qid,ref['file'])
                pooled=pool.setdefault(key,dict(first=False,groups=[]))
                pooled['first'] |= ref['rank']==1
                pooled['groups'].append(dict(group=group,rank=ref['rank']))
    jobs=[]; reused=[]
    for (qid,name),p in sorted(pool.items()):
        s=standards[qid]
        source=AUDIT/'source_text'/(name+'.txt')
        text=norm(source.read_text(encoding='utf-8-sig'))
        text_hash=hashlib.sha256(text.encode()).hexdigest()
        old=old_reviews.get((qid,name))
        if old:
            assert old['job']['text_hash']==text_hash
            assert old['job']['question']==s['question'] and old['job']['acceptance']==s['acceptance']
        adj=adjudicated.get((qid,name))
        completed=old and old.get('support') is not None and all(v.get('coverage')!='uncertain' for v in old.get('reviews',[]))
        enough=old and (not p['first'] or len(old.get('reviews',[]))>=2)
        if adj or (completed and enough):
            reused.append(dict(query_id=qid,file=name,support=adj['support'] if adj else old['support'],
                               source='baseline_adjudication' if adj else 'baseline_support_review',
                               text_hash=text_hash,second_check_required=p['first']))
            continue
        jid=hashlib.sha256((qid+'|'+name).encode()).hexdigest()[:20]
        job=dict(id=jid,query_id=qid,question=s['question'],file=name,
                 expected_facts=s['gold_answer'],acceptance=s['acceptance'],text_hash=text_hash,
                 source_text_sha256=sha(source),second_check_required=p['first'],
                 prior_reviews=old.get('reviews',[]) if completed else [])
        save(HERE/'review_inputs/jobs'/f'{jid}.json',job)
        (HERE/'review_inputs/texts').mkdir(parents=True,exist_ok=True)
        (HERE/'review_inputs/texts'/(text_hash+'.txt')).write_text(text,encoding='utf-8')
        jobs.append(job)
    save(HERE/'review_inputs/jobs.json',jobs)
    save(HERE/'scoring_inputs/reused_support.json',reused)
    save(HERE/'scoring_inputs/pooled_references.json',
         [dict(query_id=k[0],file=k[1],**v) for k,v in pool.items()])
    summary=dict(groups=list(groups),pooled_unlisted_associations=len(pool),reused=len(reused),
                 new_or_upgraded_jobs=len(jobs),upgrades=sum(bool(j['prior_reviews']) for j in jobs))
    save(HERE/'review_inputs/manifest.json',summary)
    print(json.dumps(summary))


if __name__=='__main__': main()
