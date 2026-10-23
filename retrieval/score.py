"""Score fixed ordered document lists against verified and reviewed source support."""
import csv
import json
import statistics
from pathlib import Path

HERE=Path(__file__).resolve().parent


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def write_csv(path,rows):
    if not rows: return
    with path.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]))
        w.writeheader(); w.writerows(rows)


def support_at(values,k):
    values=values[:k]
    if True in values: return True
    if None in values: return None
    return False


def measure(values):
    return dict(n=len(values),hits=sum(v is True for v in values),
                unknown=sum(v is None for v in values),
                lower_pct=round(100*sum(v is True for v in values)/len(values),2) if values else None,
                upper_pct=round(100*sum(v is not False for v in values)/len(values),2) if values else None)


def main():
    standards={s['id']:s for s in read(HERE/'inputs/standards.json')}
    results={r['query_id']:r for r in (read(p) for p in (HERE/'results/basic120/queries').glob('*.json'))}
    assert set(results)==set(standards),f'Need exactly all 120 questions; found {len(results)}'
    reviews={}
    for p in (HERE/'support_reviews').glob('*.json'):
        r=read(p)
        reviews[(r['job']['query_id'],r['job']['file'])]=r['support']
    # Explicit source-grounded adjudications override unresolved screening votes.
    adjudications=HERE/'support_reviews/adjudications.jsonl'
    if adjudications.exists():
        for line in adjudications.read_text(encoding='utf-8').splitlines():
            a=json.loads(line); reviews[(a['query_id'],a['file'])]=a['support']
    output=HERE/'reports/basic120'
    output.mkdir(parents=True,exist_ok=True)
    rows=[]; refs=[]; negatives=[]; cross=[]
    for qid,s in standards.items():
        r=results[qid]
        files=[x['file'] for x in r['references']]
        assert [x['rank'] for x in r['references']]==list(range(1,len(files)+1))
        assert len(files)==len(set(files))<=10
        values=[True if f in s['known_supporting_sources'] else reviews.get((qid,f)) for f in files]
        error=r['status'] not in {'ok','empty_retrieval'}
        row=dict(id=qid,type=s['type'],pair_id=s['pair_id'],scope=s['scope'],status=r['status'],
                 reference_count=len(files),top1_file=files[0] if files else '',
                 verified_sources=';'.join(s['known_supporting_sources']),elapsed_s=r['elapsed_s'])
        for k in [1,5,10]:
            row[f'known_source_hit_at_{k}']=any(f in s['known_supporting_sources'] for f in files[:k]) if s['scope']=='single_document' else ''
            row[f'document_hit_at_{k}']=(False if error else support_at(values,k)) if s['scope']=='single_document' else ''
        rows.append(row)
        for i,f in enumerate(files):
            refs.append(dict(id=qid,rank=i+1,file=f,verified_source=f in s['known_supporting_sources'],
                 document_support=values[i] if s['scope']=='single_document' else '',
                 support_method=('verified_source_audit' if f in s['known_supporting_sources'] else
                                 'returned_document_review' if (qid,f) in reviews else 'not_assessed')))
        if s['scope'] in {'required_combination','thematic_examples'}:
            required=set(s['required_sources'])
            item=dict(id=qid,scope=s['scope'],required_count=len(required),required_sources=';'.join(sorted(required)))
            for k in [1,5,10]:
                found=set(files[:k])&required
                item[f'found_at_{k}']=len(found)
                item[f'coverage_at_{k}']=len(found)/len(required)
                item[f'complete_at_{k}']=found==required and not error
            cross.append(item)
        if s['scope']=='negative':
            negatives.append(dict(id=qid,question=s['question'],top1_file=files[0] if files else '',
                returned_count=len(files),returned_files=';'.join(files),prior_absence_finding=s['acceptance'],
                interpretation='Document suggestions only; no answer or answerability decision produced'))
    row_map={r['id']:r for r in rows}
    pairs=[]
    for pair_id in sorted({s['pair_id'] for s in standards.values() if s['pair_id']}):
        members=[s for s in standards.values() if s['pair_id']==pair_id]
        assert len(members)==2
        a=next(s for s in members if s['type']=='pair_a'); b=next(s for s in members if s['type']=='pair_b')
        item=dict(pair_id=pair_id,a=a['id'],b=b['id'])
        for label,current,other in [('a',a,b),('b',b,a)]:
            row=row_map[current['id']]
            item[label+'_top1_file']=row['top1_file']
            own=set(current['known_supporting_sources']); opposite=set(other['known_supporting_sources'])-own
            files=[r['file'] for r in results[current['id']]['references']]
            item[label+'_opposite_source_first']=bool(files and files[0] in opposite and row['document_hit_at_1'] is not True)
            item[label+'_opposite_source_in_top10']=bool(set(files)&opposite)
            for k in [1,5,10]: item[f'{label}_hit_at_{k}']=row[f'document_hit_at_{k}']
        for k in [1,5,10]:
            item[f'both_hit_at_{k}']=item[f'a_hit_at_{k}'] is True and item[f'b_hit_at_{k}'] is True
        pairs.append(item)
    single=[r for r in rows if r['scope']=='single_document']
    calls=[json.loads(line) for p in sorted((HERE/'results/basic120').glob('calls*.jsonl'))
           for line in p.read_text(encoding='utf-8').splitlines()]
    successful_calls=[c for c in calls if c['status']=='ok']
    completion=read(HERE/'results/basic120/complete.json')
    summary=dict(questions=len(rows),single_document=len(single),cross_document=len(cross),unanswerable=len(negatives),
                 top_k={str(k):measure([r[f'document_hit_at_{k}'] for r in single]) for k in [1,5,10]},
                 known_source_top_k={str(k):measure([r[f'known_source_hit_at_{k}'] for r in single]) for k in [1,5,10]},
                 by_type={t:{str(k):measure([r[f'document_hit_at_{k}'] for r in single if r['type']==t]) for k in [1,5,10]}
                          for t in sorted({r['type'] for r in single})},
                 required_combinations={str(k):dict(n=12,complete=sum(r[f'complete_at_{k}'] for r in cross if r['scope']=='required_combination'),
                          mean_source_coverage=statistics.mean(r[f'coverage_at_{k}'] for r in cross if r['scope']=='required_combination')) for k in [1,5,10]},
                 pairs=dict(n=len(pairs),both_correct={str(k):sum(p[f'both_hit_at_{k}'] for p in pairs) for k in [1,5,10]},
                            opposite_source_first=sum(p['a_opposite_source_first']+p['b_opposite_source_first'] for p in pairs)),
                 statuses={s:sum(r['status']==s for r in rows) for s in {r['status'] for r in rows}},
                 latency=dict(median_s=statistics.median(r['elapsed_s'] for r in rows),total_query_s=sum(r['elapsed_s'] for r in rows)),
                 recovery=dict(retained_queries=len(completion.get('retained_query_ids',[])),
                               recovered_queries=len(completion.get('recovered_query_ids',[]))),
                 runtime=dict(calls=len(calls),successful_calls=len(successful_calls),models=sorted({r.get('response_model','missing') for r in successful_calls}),
                    phases={p:sum(c['phase']==p for c in calls) for p in {c['phase'] for c in calls}},
                    errors=sum(c['status']!='ok' for c in calls),
                    all_successful_http_and_response_models_match=bool(successful_calls) and all(c.get('model_match') and c.get('outbound_http_models')==[c['requested_model']] for c in successful_calls),
                    tokens={k:sum(c.get('usage',{}).get(k,0) or 0 for c in calls) for k in ['prompt_tokens','completion_tokens','total_tokens']}))
    write_csv(output/'questions.csv',rows)
    write_csv(output/'references.csv',refs)
    write_csv(output/'cross_document.csv',cross)
    write_csv(output/'pairs.csv',pairs)
    write_csv(output/'unanswerable.csv',negatives)
    (output/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    print(json.dumps(summary,indent=2))


if __name__=='__main__':
    main()
