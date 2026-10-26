"""Validate a fresh retrieval pass and its paired reranking output offline."""
import csv
import hashlib
import json
from pathlib import Path
from common import HERE,read,save,sha,ordered_ids

def main():
    checks=[]
    def check(name,value): checks.append(dict(name=name,passed=bool(value)))
    freeze=read(HERE/'freeze.json');expected=dict(freeze['files'])
    repair=read(HERE/'execution_repair/revision.json')
    check('repair_preserves_original_code_provenance',all(expected[n]==v['before_sha256']==sha(HERE/v['original_copy']) for n,v in repair['changes'].items()))
    expected.update({n:v['after_sha256'] for n,v in repair['changes'].items()})
    check('frozen_execution_code_and_inputs',all(sha(HERE/p)==v for p,v in expected.items()))
    for part in ['scan','rerank']:
        check(part+'_frozen_inputs_match',all(sha(HERE/p)==v for p,v in read(HERE/(part+'_freeze.json'))['files'].items()))
    scoring=read(HERE/'scoring_freeze.json')
    check('scoring_inputs_unchanged',all(sha(HERE/p)==v for p,v in scoring['files'].items()))
    check('prior_source_checks_unchanged',all(sha(HERE.parent.parent/p)==v for p,v in scoring['dependencies'].items()))
    corpus=read(HERE/'inputs/corpus.json');queries=read(HERE/'inputs/queries.json');ids={q['id'] for q in queries}
    standards={s['id']:s for s in read(HERE/'scoring_inputs/standards.json')};settings=read(HERE/'settings.json')
    check('same_120_questions',len(queries)==len(ids)==120 and ids==set(standards) and sha(HERE/'inputs/queries.json')==sha(HERE.parent/'inputs/queries.json'))
    check('81_original_hashes_match',len(corpus)==81 and all(sha(HERE.parent.parent/'poc_docs/S'/r['file'])==r['sha256'] for r in corpus))
    check('one_batch_two_arms',settings['repetitions']==1 and settings['comparison_groups']==['Baseline','RR10'] and set(settings['groups'])=={'RR10'})
    fresh=read(HERE/'results/basic120/preflight.json')
    check('fresh_preparation_record',fresh['model_preflight_passed'] and fresh['corpus_hashes_match'] and fresh['scan_files']==81 and read(HERE/'scan_freeze.json')['fresh_cache'])
    check('installed_source_identity_record',fresh['source_hashes']==read(HERE/'inputs/source_hashes.json'))
    check('first_native_result_preserved',sha(HERE/'results/basic120/queries/INV-01.json')==repair['native_result_sha256'] and sha(HERE/'runs/Baseline/queries/INV-01.json')==repair['recovered_result_sha256'])
    for checkpoint in sorted((HERE/'recovery').glob('*.json')):
        check('completed_results_preserved_'+checkpoint.stem,all(sha(HERE/p)==v for p,v in read(checkpoint)['files'].items()))
    groups={g:{p.stem:read(p) for p in (HERE/'runs'/g/'queries').glob('*.json')} for g in ['Baseline','RR10']}
    all_calls=[]
    for group,records in groups.items():
        cr=[json.loads(line) for p in (HERE/'runs'/group).glob('calls*.jsonl') for line in p.read_text(encoding='utf-8').splitlines()]
        all_calls.extend(cr)
        check(group+'_all_120_completed',set(records)==ids)
        check(group+'_runtime_identity',all(c.get('requested_model')==c.get('response_model')==settings['model'] and c.get('outbound_http_models')==[settings['model']] for c in cr if c['status']=='ok'))
        check(group+'_phases',set(c['phase'] for c in cr)<=({'keywords','directory'} if group=='Baseline' else {'rerank'}))
        check(group+'_no_answers_or_clusters',all(r['answer_generated'] is False and r['cluster_used'] is False and r['evidence_sampling'] is False and 'answer' not in r for r in records.values()))
        check(group+'_rank_and_unique_files',all([v['rank'] for v in r['references']]==list(range(1,len(r['references'])+1)) and len({v['file'] for v in r['references']})==len(r['references'])<=10 for r in records.values()))
        attempts=[read(p) for p in (HERE/'runs'/group/'attempts').glob('*/*.json')]
        check(group+'_attempt_limit',all(sum(a['query_id']==qid for a in attempts)<=3 for qid in ids))
    check('fresh_keyword_requests_for_every_query',{c['query_id'] for c in all_calls if c['phase']=='keywords'}==ids)
    check('fresh_directory_requests_for_every_query',{c['query_id'] for c in all_calls if c['phase']=='directory'}==ids)
    old_ids=set()
    historical=[HERE.parent/'results/basic120',HERE.parent/'followup120/runs',HERE.parent/'rerank_top5_top10/runs']
    for folder in historical:
        for p in folder.rglob('calls*.jsonl'):
            for line in p.read_text(encoding='utf-8').splitlines():
                c=json.loads(line)
                if c.get('response_id'):old_ids.add(c['response_id'])
    check('new_requests_not_historical_responses',not ({c['response_id'] for c in all_calls if c.get('response_id')} & old_ids))
    native=True;candidate_match=True;trace=True;payload_safe=True
    scan={c['filename']:c for c in read(HERE/'inputs/directory_scan.json')['candidates']}
    docids=read(HERE/'inputs/document_ids.json')
    by_response={c['response_id']:c for c in all_calls if c.get('response_id')}
    for q in queries:
        qid=q['id'];base=groups['Baseline'][qid];ranked=groups['RR10'][qid]
        bf=[v['file'] for v in base['references']];rf=[v['file'] for v in ranked['references']]
        native &= base['status']=='technical_failure' or [r['path'] for r in base['references']]==list(dict.fromkeys(base['keyword_files']+base['directory_files']))[:10]
        native &= sha(HERE/'baseline'/(qid+'.json'))==sha(HERE/'runs/Baseline/queries'/(qid+'.json'))
        candidate_match &= len(bf)==len(rf) and set(bf)==set(rf)
        pp=HERE/'inputs/payloads/RR10'/(qid+'.json');payload=read(pp)
        ordered=sorted(bf,key=lambda name:hashlib.sha256(f"{settings['presentation_seed']}|{qid}|{name}".encode()).hexdigest())
        payload_safe &= set(payload)=={'question','documents'} and payload['question']==q['question'] and [d['file'] for d in payload['documents']]==ordered
        for d in payload['documents']:
            c=scan[d['file']]
            payload_safe &= d==dict(id=docids[d['file']],file=d['file'],title=c.get('title') or '',keywords=c.get('keywords') or [],preview=(c.get('preview') or '')[:800])
        trace &= ranked['baseline_sha256']==sha(HERE/'baseline'/(qid+'.json')) and ranked['payload_sha256']==sha(pp)
        if ranked['status']=='ok':
            successes=[read(p) for p in (HERE/'runs/RR10/attempts'/qid).glob('*.json') if read(p)['status']=='ok']
            trace &= len(successes)==1
            if len(successes)==1:
                c=by_response[successes[0]['response_id']];mapping={d['id']:d['file'] for d in payload['documents']}
                output=ordered_ids(json.loads(c['response_text']),mapping)
                trace &= rf==[mapping[x] for x in output]
                messages=[{'role':'system','content':(HERE/'prompt.txt').read_text(encoding='utf-8')},{'role':'user','content':json.dumps(payload,ensure_ascii=False)}]
                trace &= c['prompt_sha256']==hashlib.sha256(json.dumps(messages,sort_keys=True).encode()).hexdigest()
        else:trace &= rf==bf
    check('native_retrieval_order_and_same_batch_baseline',native)
    check('reranking_preserves_exact_candidate_sets',candidate_match)
    check('ranking_inputs_blinded_and_preview_limited',payload_safe)
    check('ranking_response_trace_matches',trace)
    rows=list(csv.DictReader((HERE/'reports/questions.csv').open(encoding='utf-8',newline='')));lookup={(r['group'],r['id']):r for r in rows}
    summary=read(HERE/'reports/summary.json')
    check('240_scored_results',len(rows)==len(lookup)==240)
    check('top10_invariant_per_query',all(lookup['Baseline',qid]['hit_at_10']==lookup['RR10',qid]['hit_at_10'] for qid in ids))
    check('98_primary_denominator',all(h['n']==98 for g in summary['groups'].values() for h in g['hits'].values()))
    check('no_unresolved_primary_scores',all(h['unknown']==0 for g in summary['groups'].values() for h in g['hits'].values()))
    check('rerank_ceiling',summary['groups']['RR10']['hits']['1']['hits']<=summary['groups']['Baseline']['hits']['10']['hits'])
    reused={(r['query_id'],r['file']):r for r in read(HERE/'scoring_inputs/reused_support.json')}
    reviewed={}
    for p in (HERE/'support_reviews').glob('*.json'):
        r=read(p)
        if 'job' in r: reviewed[r['job']['query_id'],r['job']['file']]=r
    adj={}
    ap=HERE/'support_reviews/adjudications.jsonl'
    if ap.exists():
        for line in ap.read_text(encoding='utf-8').splitlines():
            r=json.loads(line);adj[r['query_id'],r['file']]=r
    adjudication_grounded=True
    for k,r in adj.items():
        text=(HERE/'review_inputs/texts'/(r['text_hash']+'.txt')).read_text(encoding='utf-8')
        adjudication_grounded &= hashlib.sha256(text.encode()).hexdigest()==r['text_hash']
        adjudication_grounded &= k in reviewed and reviewed[k]['job']['text_hash']==r['text_hash']
        adjudication_grounded &= bool(r['evidence']) and all(
            0<=e['start']<e['end']<=len(text) and text[e['start']:e['end']]==e['quote'] for e in r['evidence'])
    check('adjudication_evidence_matches_source',adjudication_grounded)
    enough=True
    for r in rows:
        if r['scope']!='single_document' or not r['top1_file'] or r['top1_file'] in standards[r['id']]['known_supporting_sources']:continue
        k=r['id'],r['top1_file']
        if k in adj:continue
        if k in reused: enough &= reused[k]['adjudicated'] or reused[k]['review_count']>=2
        else: enough &= k in reviewed and reviewed[k]['support'] is not None and len(reviewed[k]['reviews'])>=2
    check('first_position_exceptions_checked',enough)
    jobs=read(HERE/'review_inputs/jobs.json')
    check('all_source_jobs_completed',{(j['query_id'],j['file']) for j in jobs}==set(reviewed))
    check('additional_positives_grounded',all(len(r['reviews'])==2 and all(v.get('coverage')=='full' and v.get('identity')=='correct' and v.get('all_quotes_grounded') for v in r['reviews']) for r in reviewed.values() if r['support'] is True))
    check('ungrounded_or_uncertain_reviews_adjudicated',all(k in adj for k,r in reviewed.items() if r['support'] is None or any(v.get('all_quotes_grounded') is False for v in r['reviews'])))
    sc=[json.loads(line) for p in (HERE/'support_reviews').glob('calls*.jsonl') for line in p.read_text(encoding='utf-8').splitlines()]
    check('source_runtime_matches',all(c.get('requested_model')==c.get('response_model')==settings['model'] and c.get('outbound_http_models')==[settings['model']] and c['phase']=='support_review' for c in sc if c['status']=='ok'))
    preflight=[json.loads(line) for p in [HERE/'preflight_calls.jsonl',HERE/'results/basic120/preflight_calls.jsonl'] for line in p.read_text(encoding='utf-8').splitlines()]
    check('preflight_runtime_matches',bool(preflight) and all(c.get('requested_model')==c.get('response_model')==settings['model'] and c.get('outbound_http_models')==[settings['model']] for c in preflight if c['status']=='ok'))
    result=dict(checks=len(checks),passed=sum(c['passed'] for c in checks),all_passed=all(c['passed'] for c in checks),details=checks)
    save(HERE/'reports/validation.json',result)
    print(json.dumps(dict(checks=result['checks'],passed=result['passed'],failed=[c['name'] for c in checks if not c['passed']]),indent=2))
    if not result['all_passed']:raise SystemExit(1)

if __name__=='__main__':main()
