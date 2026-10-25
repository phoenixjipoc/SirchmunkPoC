"""Score pooled source support, paired changes and repeated-run stability."""
import csv
import json
import statistics
from collections import Counter,defaultdict
from pathlib import Path
from prepare_support import HERE,BASE,read,save,results


def csvout(path,rows):
    if not rows: return
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)


def hit(values,k):
    if True in values[:k]: return True
    if None in values[:k]: return None
    return False


def measure(values):
    return dict(n=len(values),hits=sum(v is True for v in values),unknown=sum(v is None for v in values),
                lower_pct=round(100*sum(v is True for v in values)/len(values),2) if values else None,
                upper_pct=round(100*sum(v is not False for v in values)/len(values),2) if values else None)


def reciprocal(values):
    definite=next((i+1 for i,v in enumerate(values) if v is True),0)
    possible=next((i+1 for i,v in enumerate(values) if v is not False),0)
    return (1/definite if definite else 0,1/possible if possible else 0)


def main():
    standards={r['id']:r for r in read(BASE/'inputs/standards.json')}
    groups=results()
    support={}
    for r in read(HERE/'scoring_inputs/reused_support.json'): support[r['query_id'],r['file']]=r['support']
    for p in (HERE/'support_reviews').glob('*.json'):
        r=read(p)
        if 'job' in r: support[r['job']['query_id'],r['job']['file']]=r['support']
    adj=HERE/'support_reviews/adjudications.jsonl'
    if adj.exists():
        for line in adj.read_text(encoding='utf-8').splitlines():
            r=json.loads(line); support[r['query_id'],r['file']]=r['support']
    opposite={}
    for s in standards.values():
        if s['pair_id']:
            other=next(t for t in standards.values() if t['pair_id']==s['pair_id'] and t['id']!=s['id'])
            opposite[s['id']]=set(other['known_supporting_sources'])-set(s['known_supporting_sources'])
    rows=[]; refs=[]; cross=[]; negatives=[]; pairs=[]; summaries={}; bydocument=[]; transitions=[]
    for group,records in groups.items():
        assert set(records)==set(standards),group
        gr=[]
        for qid,s in standards.items():
            r=records[qid]; files=[x['file'] for x in r['references']]
            assert len(files)==len(set(files))<=10
            assert [x['rank'] for x in r['references']]==list(range(1,len(files)+1))
            valid=r['status'] in {'ok','empty_retrieval'}
            values=[True if f in s['known_supporting_sources'] else support.get((qid,f)) for f in files]
            if not valid: values=[False]*len(files)
            lower,upper=reciprocal(values)
            knownrank=next((i+1 for i,f in enumerate(files) if f in s['known_supporting_sources']),0)
            first=next((i+1 for i,v in enumerate(values) if v is True),0)
            allfiles=[Path(p).name for p in r.get('merged_files',[])]
            known_candidate=next((i+1 for i,f in enumerate(allfiles) if f in s['known_supporting_sources']),0)
            cause='not_single_document'
            if s['scope']=='single_document':
                if not valid: cause='technical_failure'
                elif not files: cause='empty_retrieval'
                elif values[0] is True: cause='top1_hit'
                elif values[0] is None: cause='unresolved_top1_support'
                elif first: cause='support_rank_2_5' if first<=5 else 'support_rank_6_10'
                elif None in values: cause='unresolved_support'
                elif group=='S':
                    original=groups['R1'][qid]
                    basefiles=[Path(p).name for p in original.get('merged_files',[])]
                    cause='outside_fixed_candidate_pool' if set(basefiles)&set(s['known_supporting_sources']) else 'absent_from_candidates'
                elif known_candidate>10: cause='beyond_cutoff'
                else: cause='absent_from_candidates'
            row=dict(group=group,id=qid,type=s['type'],pair_id=s['pair_id'],scope=s['scope'],status=r['status'],
                     top1_file=files[0] if files else '',reference_count=len(files),first_supported_rank=first or '',
                     known_source_rank=knownrank or '',known_candidate_rank=known_candidate or '',
                     mrr10_lower=lower if s['scope']=='single_document' else '',
                     mrr10_upper=upper if s['scope']=='single_document' else '',
                     opposite_source_first=bool(files and files[0] in opposite.get(qid,set()) and values[0] is not True),
                     failure_category=cause,elapsed_s=r['elapsed_s'])
            for k in [1,5,10]: row[f'hit_at_{k}']=hit(values,k) if s['scope']=='single_document' else ''
            rows.append(row); gr.append(row)
            for i,f in enumerate(files):
                refs.append(dict(group=group,id=qid,rank=i+1,file=f,
                                 support=values[i] if s['scope']=='single_document' else '',
                                 known_source=f in s['known_supporting_sources']))
            if s['scope'] in {'required_combination','thematic_examples'}:
                needed=set(s['required_sources'])
                for k in [1,5,10]:
                    found=set(files[:k])&needed if valid else set()
                    cross.append(dict(group=group,id=qid,scope=s['scope'],k=k,required_count=len(needed),
                                      found_count=len(found),coverage=len(found)/len(needed),complete=found==needed))
            if s['scope']=='negative':
                negatives.append(dict(group=group,id=qid,reference_count=len(files),top1_file=files[0] if files else '',
                                      files=';'.join(files),interpretation='Suggestions only; no answerability decision'))
        single=[r for r in gr if r['scope']=='single_document']
        for source in sorted({f for s in standards.values() if s['scope']=='single_document' for f in s['known_supporting_sources']}):
            docrows=[r for r in single if source in standards[r['id']]['known_supporting_sources']]
            bydocument.append(dict(group=group,file=source,questions=len(docrows),
                 top1_lower_pct=measure([r['hit_at_1'] for r in docrows])['lower_pct'],
                 top1_upper_pct=measure([r['hit_at_1'] for r in docrows])['upper_pct'],
                 mrr10_lower=statistics.mean(r['mrr10_lower'] for r in docrows)))
        for pid in sorted({r['pair_id'] for r in single if r['pair_id']}):
            members=[r for r in single if r['pair_id']==pid]
            item=dict(group=group,pair_id=pid,ids=';'.join(r['id'] for r in members))
            for k in [1,5,10]: item[f'both_at_{k}']=all(r[f'hit_at_{k}'] is True for r in members)
            item['opposite_first']=sum(r['opposite_source_first'] for r in members)
            pairs.append(item)
        callpaths=list((HERE/'runs'/group).glob('calls*.jsonl')) if group!='R1' else list((BASE/'results/basic120').glob('calls*.jsonl'))
        calls=[json.loads(line) for p in callpaths for line in p.read_text(encoding='utf-8').splitlines()]
        searchcalls=[c for c in calls if c['phase']!='preflight']
        attempts=[read(p) for p in (HERE/'runs'/group/'attempts').glob('*/*.json')]
        failed_attempts=[r for r in attempts if r['status'] not in {'ok','empty_retrieval'}]
        summaries[group]=dict(questions=len(gr),single_document=len(single),
            hits={str(k):measure([r[f'hit_at_{k}'] for r in single]) for k in [1,5,10]},
            mrr10_lower=statistics.mean(r['mrr10_lower'] for r in single),
            mrr10_upper=statistics.mean(r['mrr10_upper'] for r in single),
            macro_document_top1_lower_pct=statistics.mean(r['top1_lower_pct'] for r in bydocument if r['group']==group),
            by_type={t:{str(k):measure([r[f'hit_at_{k}'] for r in single if r['type']==t]) for k in [1,5,10]}
                     for t in sorted({r['type'] for r in single})},
            failures=dict(Counter(r['failure_category'] for r in single)),
            statuses=dict(Counter(r['status'] for r in gr)),
            pairs_both={str(k):sum(r[f'both_at_{k}'] for r in pairs if r['group']==group) for k in [1,5,10]},
            opposite_first=sum(r['opposite_source_first'] for r in single),
            required_combinations={str(k):dict(n=12,complete=sum(r['complete'] for r in cross if r['group']==group and r['scope']=='required_combination' and r['k']==k),
                mean_coverage=statistics.mean(r['coverage'] for r in cross if r['group']==group and r['scope']=='required_combination' and r['k']==k)) for k in [1,5,10]},
            median_query_s=statistics.median(r['elapsed_s'] for r in gr),
            completed_query_s=sum(r['elapsed_s'] for r in gr),
            calls=len(searchcalls),call_errors=sum(c.get('status')!='ok' for c in searchcalls),
            incomplete_call_records=sum('status' not in c for c in searchcalls),
            technical_attempts=len(failed_attempts),
            technical_attempt_seconds=sum(r['elapsed_s'] for r in failed_attempts),
            preflight_calls=sum(c['phase']=='preflight' for c in calls),
            preflight_tokens=sum(c.get('usage',{}).get('total_tokens',0) or 0 for c in calls if c['phase']=='preflight'),
            total_tokens=sum(c.get('usage',{}).get('total_tokens',0) or 0 for c in searchcalls),
            successful_models=sorted({c.get('response_model') for c in searchcalls if c.get('status')=='ok'}))
    lookup={(r['group'],r['id']):r for r in rows}
    stability=[]
    for qid,s in standards.items():
        if s['scope']!='single_document': continue
        repeats=[lookup[g,qid] for g in ['R1','R2','R3']]
        v=[r['hit_at_1'] for r in repeats]
        stability.append(dict(id=qid,type=s['type'],top1_hits=sum(x is True for x in v),unknown=sum(x is None for x in v),
                              all_hit=all(x is True for x in v),all_miss=all(x is False for x in v),
                              correctness_changes=True in v and False in v,
                              top1_file_changes=len({r['top1_file'] for r in repeats})>1,
                              first_files=' | '.join(r['top1_file'] for r in repeats)))
    for group in [g for g in groups if g!='R1']:
        comparator='P0' if group=='P' else 'R1'
        for qid,s in standards.items():
            if s['scope']!='single_document': continue
            before,after=lookup[comparator,qid],lookup[group,qid]
            transitions.append(dict(group=group,comparator=comparator,id=qid,type=s['type'],
                before_hit1=before['hit_at_1'],after_hit1=after['hit_at_1'],
                gain=before['hit_at_1'] is False and after['hit_at_1'] is True,
                loss=before['hit_at_1'] is True and after['hit_at_1'] is False,
                before_rank=before['first_supported_rank'],after_rank=after['first_supported_rank'],
                before_file=before['top1_file'],after_file=after['top1_file']))
    output=HERE/'reports'; output.mkdir(exist_ok=True)
    for name,data in [('questions',rows),('references',refs),('cross_document',cross),('unanswerable',negatives),
                      ('pairs',pairs),('by_document',bydocument),('stability',stability),('transitions',transitions)]:
        csvout(output/(name+'.csv'),data)
    summary=dict(groups=summaries,stability=dict(n=98,
        all_three_hit=sum(r['all_hit'] for r in stability),all_three_miss=sum(r['all_miss'] for r in stability),
        correctness_changes=sum(r['correctness_changes'] for r in stability),top1_file_changes=sum(r['top1_file_changes'] for r in stability),
        unknown=sum(r['unknown'] for r in stability),
        mean_top1_pct=statistics.mean(summaries[g]['hits']['1']['lower_pct'] for g in ['R1','R2','R3']),
        min_top1_pct=min(summaries[g]['hits']['1']['lower_pct'] for g in ['R1','R2','R3']),
        max_top1_pct=max(summaries[g]['hits']['1']['lower_pct'] for g in ['R1','R2','R3'])),
        matched={g:dict(gains=sum(r['gain'] for r in transitions if r['group']==g),losses=sum(r['loss'] for r in transitions if r['group']==g))
                 for g in groups if g!='R1'})
    review_calls=[json.loads(line) for p in (HERE/'support_reviews').glob('calls*.jsonl')
                  for line in p.read_text(encoding='utf-8').splitlines()]
    summary['source_check_usage']=dict(calls=len(review_calls),errors=sum(r.get('status')!='ok' for r in review_calls),
        total_tokens=sum(r.get('usage',{}).get('total_tokens',0) or 0 for r in review_calls),
        completion=read(HERE/'support_complete.json') if (HERE/'support_complete.json').exists() else None)
    save(output/'summary.json',summary)
    print(json.dumps({g:{'top1':v['hits']['1'],'top10':v['hits']['10'],'mrr10':v['mrr10_lower']} for g,v in summaries.items()},indent=2))


if __name__=='__main__': main()
