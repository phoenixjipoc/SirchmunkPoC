"""Calculate paired document-support measures from the frozen experiment."""
import csv
import json
import math
import statistics
from collections import Counter
from common import HERE, read, save

def csvout(name, rows):
    if not rows:
        return
    p=HERE/'reports'/(name+'.csv'); p.parent.mkdir(exist_ok=True)
    with p.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)

def hit(values,k):
    if True in values[:k]: return True
    if None in values[:k]: return None
    return False

def measure(values):
    n=len(values); hits=sum(x is True for x in values); unknown=sum(x is None for x in values)
    return dict(n=n,hits=hits,unknown=unknown,lower_pct=round(100*hits/n,2),upper_pct=round(100*(hits+unknown)/n,2))

def rank(values,possible=False):
    return next((i+1 for i,v in enumerate(values) if (v is not False if possible else v is True)),0)

def calls(folder):
    return [json.loads(line) for p in folder.glob('calls*.jsonl') for line in p.read_text(encoding='utf-8').splitlines()]

def latency(values):
    return dict(n=len(values),median_s=round(statistics.median(values),3) if values else None,
        p95_s=round(sorted(values)[math.ceil(.95*len(values))-1],3) if values else None)

def main():
    standards={s['id']:s for s in read(HERE/'scoring_inputs/standards.json')}
    support={(r['query_id'],r['file']):r['support'] for r in read(HERE/'scoring_inputs/reused_support.json')}
    for p in (HERE/'support_reviews').glob('*.json'):
        r=read(p)
        if 'job' in r: support[r['job']['query_id'],r['job']['file']]=r['support']
    adj=HERE/'support_reviews/adjudications.jsonl'
    if adj.exists():
        for line in adj.read_text(encoding='utf-8').splitlines():
            r=json.loads(line); support[r['query_id'],r['file']]=r['support']
    opposite={s['id']:set(t['known_supporting_sources'])-set(s['known_supporting_sources'])
        for s in standards.values() if s['pair_id'] for t in standards.values()
        if t['pair_id']==s['pair_id'] and t['id']!=s['id']}
    rows=[]; refs=[]; combinations=[]; negatives=[]; pairs=[]; summaries={}; documents=[]
    for group in ['Baseline','RR5','RR10']:
        folder=HERE/'baseline' if group=='Baseline' else HERE/'runs'/group/'queries'
        records={p.stem:read(p) for p in folder.glob('*.json')}
        assert set(records)==set(standards)
        group_rows=[]
        for qid,s in standards.items():
            r=records[qid]; files=[x['file'] for x in r['references']]
            values=[True if name in s['known_supporting_sources'] else support.get((qid,name)) for name in files]
            first=rank(values); possible=rank(values,True)
            single=s['scope']=='single_document'
            row=dict(group=group,id=qid,type=s['type'],pair_id=s['pair_id'],scope=s['scope'],status=r['status'],
                reference_count=len(files),top1_file=files[0] if files else '',first_supported_rank=first or '',
                hit_at_1=hit(values,1) if single else '',hit_at_5=hit(values,5) if single else '',hit_at_10=hit(values,10) if single else '',
                mrr10_lower=(1/first if first else 0) if single else '',mrr10_upper=(1/possible if possible else 0) if single else '',
                opposite_source_first=bool(single and files and files[0] in opposite.get(qid,set()) and values[0] is not True),
                rerank_seconds=r.get('elapsed_s',0) if group!='Baseline' else '')
            rows.append(row); group_rows.append(row)
            for i,name in enumerate(files):
                refs.append(dict(group=group,id=qid,rank=i+1,file=name,support=values[i] if single else '',
                    known_source=name in s['known_supporting_sources']))
            if s['scope'] in {'required_combination','thematic_examples'}:
                needed=set(s['required_sources'])
                for k in [1,5,10]:
                    found=needed & set(files[:k])
                    combinations.append(dict(group=group,id=qid,scope=s['scope'],k=k,required_count=len(needed),
                        found_count=len(found),coverage=len(found)/len(needed),complete=found==needed))
            if s['scope']=='negative':
                negatives.append(dict(group=group,id=qid,reference_count=len(files),top1_file=files[0] if files else '',
                    files=';'.join(files),interpretation='Document suggestions; no answerability decision'))
        single=[r for r in group_rows if r['scope']=='single_document']
        for pid in sorted({r['pair_id'] for r in single if r['pair_id']}):
            members=[r for r in single if r['pair_id']==pid]
            pairs.append(dict(group=group,pair_id=pid,ids=';'.join(r['id'] for r in members),
                both_at_1=all(r['hit_at_1'] is True for r in members),both_at_5=all(r['hit_at_5'] is True for r in members),
                both_at_10=all(r['hit_at_10'] is True for r in members),opposite_first=sum(r['opposite_source_first'] for r in members)))
        for name in sorted({f for s in standards.values() if s['scope']=='single_document' for f in s['known_supporting_sources']}):
            matched=[r for r in single if name in standards[r['id']]['known_supporting_sources']]
            documents.append(dict(group=group,file=name,questions=len(matched),top1_lower_pct=measure([r['hit_at_1'] for r in matched])['lower_pct']))
        cr=calls(HERE/'runs'/group) if group!='Baseline' else []
        summaries[group]=dict(questions=len(group_rows),hits={str(k):measure([r[f'hit_at_{k}'] for r in single]) for k in [1,5,10]},
            mrr10_lower=statistics.mean(r['mrr10_lower'] for r in single),mrr10_upper=statistics.mean(r['mrr10_upper'] for r in single),
            macro_document_top1_lower_pct=statistics.mean(r['top1_lower_pct'] for r in documents if r['group']==group),
            by_type={t:{str(k):measure([r[f'hit_at_{k}'] for r in single if r['type']==t]) for k in [1,5,10]}
                for t in sorted({r['type'] for r in single})},
            statuses=dict(Counter(r['status'] for r in group_rows)),
            pairs_both={str(k):sum(r[f'both_at_{k}'] for r in pairs if r['group']==group) for k in [1,5,10]},
            opposite_first=sum(r['opposite_source_first'] for r in single),
            combinations={str(k):dict(complete=sum(r['complete'] for r in combinations if r['group']==group and r['scope']=='required_combination' and r['k']==k),
                mean_coverage=statistics.mean(r['coverage'] for r in combinations if r['group']==group and r['scope']=='required_combination' and r['k']==k)) for k in [1,5,10]},
            thematic={str(k):sum(r['found_count'] for r in combinations if r['group']==group and r['scope']=='thematic_examples' and r['k']==k) for k in [1,5,10]},
            calls=len(cr),call_errors=sum(r['status']!='ok' for r in cr),tokens=sum(r.get('usage',{}).get('total_tokens',0) or 0 for r in cr),
            prompt_tokens=sum(r.get('usage',{}).get('prompt_tokens',0) or 0 for r in cr),completion_tokens=sum(r.get('usage',{}).get('completion_tokens',0) or 0 for r in cr),
            request_latency=latency([r['elapsed_s'] for r in cr]),
            task_latency=latency([r['elapsed_s'] for r in records.values() if r.get('candidate_count',0)>1]) if group!='Baseline' else None)
    lookup={(r['group'],r['id']):r for r in rows}
    transitions=[]
    for before,after in [('Baseline','RR5'),('Baseline','RR10'),('RR5','RR10')]:
        for qid,s in standards.items():
            if s['scope']!='single_document': continue
            b,a=lookup[before,qid],lookup[after,qid]
            transitions.append(dict(comparison=before+'->'+after,id=qid,type=s['type'],before_hit1=b['hit_at_1'],after_hit1=a['hit_at_1'],
                gain=b['hit_at_1'] is False and a['hit_at_1'] is True,loss=b['hit_at_1'] is True and a['hit_at_1'] is False,
                before_rank=b['first_supported_rank'],after_rank=a['first_supported_rank'],before_file=b['top1_file'],after_file=a['top1_file']))
    matched={c:dict(gains=sum(r['gain'] for r in transitions if r['comparison']==c),losses=sum(r['loss'] for r in transitions if r['comparison']==c))
        for c in sorted({r['comparison'] for r in transitions})}
    rc=calls(HERE/'support_reviews')
    pc=[json.loads(line) for line in (HERE/'preflight_calls.jsonl').read_text(encoding='utf-8').splitlines()]
    summary=dict(groups=summaries,matched=matched,source_checks=dict(jobs=read(HERE/'review_inputs/manifest.json'),calls=len(rc),
        tokens=sum(r.get('usage',{}).get('total_tokens',0) or 0 for r in rc)),preflight=dict(calls=len(pc),tokens=sum(r.get('usage',{}).get('total_tokens',0) or 0 for r in pc)))
    for name,data in [('questions',rows),('references',refs),('pairs',pairs),('cross_document',combinations),
        ('unanswerable',negatives),('transitions',transitions),('by_document',documents)]: csvout(name,data)
    save(HERE/'reports/summary.json',summary)
    print(json.dumps({g:dict(hits=v['hits'],mrr=v['mrr10_lower']) for g,v in summaries.items()},indent=2))

if __name__=='__main__': main()
