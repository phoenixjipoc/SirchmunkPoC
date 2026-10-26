"""Offline checks of frozen inputs, request provenance and scoring invariants."""
import csv
import hashlib
import json
from common import HERE, read, sha, save, ordered_ids, apply_order

def main():
    checks=[]
    def check(name,passed):
        checks.append(dict(name=name,passed=bool(passed)))
    freeze=read(HERE/'freeze.json')
    check('execution_inputs_and_code_unchanged',all(sha(HERE/p)==v for p,v in freeze['files'].items()))
    scoring=read(HERE/'scoring_freeze.json')
    check('scoring_inputs_unchanged',all(sha(HERE/p)==v for p,v in scoring['files'].items()))
    check('reused_decision_provenance_unchanged',all(sha(HERE.parent.parent/p)==v for p,v in scoring['dependencies'].items()))
    check('environment_verified',read(HERE/'environment_validation.json')['all_passed'])
    settings=read(HERE/'settings.json'); queries=read(HERE/'inputs/queries.json')
    standards={r['id']:r for r in read(HERE/'scoring_inputs/standards.json')}
    ids={q['id'] for q in queries}
    check('120_unique_queries',len(queries)==len(ids)==120 and ids==set(standards))
    check('original_queries_unchanged',sha(HERE/'inputs/queries.json')==sha(HERE.parent/'inputs/queries.json'))
    check('98_primary_questions',sum(s['scope']=='single_document' for s in standards.values())==98)
    corpus=read(HERE/'inputs/corpus.json')
    check('81_original_documents_match',len(corpus)==81 and all(sha(HERE.parent.parent/'poc_docs/S'/r['file'])==r['sha256'] for r in corpus))
    check('baseline_byte_identical',all(sha(p)==sha(HERE.parent/'followup120/baseline'/p.name) for p in (HERE/'baseline').glob('*.json')))
    recovery=HERE/'recovery_1.json'
    if recovery.exists():
        check('completed_results_unchanged_after_recovery',all(sha(HERE/p)==v for p,v in read(recovery)['retained_hashes'].items()))
    scan={c['filename']:c for c in read(HERE/'inputs/directory_scan.json')['candidates']}
    identifiers=read(HERE/'inputs/document_ids.json')
    completed={}
    for group,limit in settings['groups'].items():
        records={p.stem:read(p) for p in (HERE/'runs'/group/'queries').glob('*.json')}
        completed[group]=records
        cr=[json.loads(line) for line in (HERE/'runs'/group/'calls.jsonl').read_text(encoding='utf-8').splitlines()]
        by_response={r.get('response_id'):r for r in cr if r['status']=='ok'}
        check(group+'_all_tasks_completed',set(records)==ids)
        check(group+'_all_calls_runtime_checked',all(c['requested_model']==c.get('response_model')==settings['model'] and c['outbound_http_models']==[settings['model']] and c.get('model_match') for c in cr if c['status']=='ok'))
        check(group+'_only_ranking_calls',all(c['phase']=='rerank' for c in cr))
        safe=True; permutation=True; grounded=True; noextras=True; equalinputs=True; retries=True
        for q in queries:
            qid=q['id']; r=records[qid]
            payload_path=HERE/'inputs/payloads'/group/(qid+'.json'); payload=read(payload_path)
            original=[v['file'] for v in read(HERE/'baseline'/(qid+'.json'))['references']]
            files=[v['file'] for v in r['references']]
            permutation &= len(set(files))==len(files)==len(original) and set(files)==set(original)
            permutation &= group!='RR5' or files[5:]==original[5:]
            permutation &= [v['rank'] for v in r['references']]==list(range(1,len(files)+1))
            noextras &= set(payload)=={'question','documents'} and payload['question']==q['question']
            safe &= not r['answer_generated'] and not r['cluster_used'] and not r['evidence_sampling']
            safe &= r['payload_sha256']==sha(payload_path) and r['baseline_sha256']==sha(HERE/'baseline'/(qid+'.json'))
            pool=original[:limit]
            ordered=sorted(pool,key=lambda name:hashlib.sha256(f"{settings['presentation_seed']}|{qid}|{name}".encode()).hexdigest())
            equalinputs &= [d['file'] for d in payload['documents']]==ordered
            for d in payload['documents']:
                c=scan[d['file']]
                equalinputs &= d==dict(id=identifiers[d['file']],file=d['file'],title=c.get('title') or '',keywords=c.get('keywords') or [],preview=(c.get('preview') or '')[:800])
                noextras &= set(d)=={'id','file','title','keywords','preview'} and len(d['preview'])<=800
            attempts=[read(p) for p in (HERE/'runs'/group/'attempts'/qid).glob('*.json')]
            retries &= len(attempts)<=3 and r['attempts']==len(attempts)
            if r['status']=='ok':
                successes=[a for a in attempts if a['status']=='ok']
                grounded &= len(successes)==1
                if len(successes)==1:
                    a=successes[0]; call=by_response.get(a['response_id'])
                    grounded &= bool(call)
                    if call:
                        mapping={d['id']:d['file'] for d in payload['documents']}
                        output=ordered_ids(json.loads(call['response_text']),mapping)
                        grounded &= files==apply_order(original,[mapping[x] for x in output],limit)==a['output_files']
                        messages=[{'role':'system','content':(HERE/'prompt.txt').read_text(encoding='utf-8')},
                                  {'role':'user','content':json.dumps(payload,ensure_ascii=False)}]
                        expected=hashlib.sha256(json.dumps(messages,sort_keys=True).encode()).hexdigest()
                        grounded &= call['prompt_sha256']==expected
            else:
                grounded &= files==original and r['status'] in {'skipped_empty','skipped_single','fallback_original'}
        check(group+'_unchanged_candidate_set_and_tail',permutation)
        check(group+'_frozen_metadata_only_payloads',noextras and equalinputs)
        check(group+'_response_to_result_trace',grounded)
        check(group+'_attempt_limits',retries)
        check(group+'_retrieval_only_and_hash_links',safe)
    equal=True
    for qid in ids:
        small=read(HERE/'inputs/payloads/RR5'/(qid+'.json'))['documents']
        large={d['file']:d for d in read(HERE/'inputs/payloads/RR10'/(qid+'.json'))['documents']}
        equal &= all(d==large[d['file']] for d in small)
    check('shared_candidates_identical_between_arms',equal)
    rows=list(csv.DictReader((HERE/'reports/questions.csv').open(encoding='utf-8',newline='')))
    lookup={(r['group'],r['id']):r for r in rows}
    check('360_scored_results',len(rows)==360 and len(lookup)==360)
    check('per_question_top10_invariant',all(lookup['Baseline',qid]['hit_at_10']==lookup['RR5',qid]['hit_at_10']==lookup['RR10',qid]['hit_at_10'] for qid in ids))
    check('rr5_per_question_top5_invariant',all(lookup['Baseline',qid]['hit_at_5']==lookup['RR5',qid]['hit_at_5'] for qid in ids))
    summary=read(HERE/'reports/summary.json')
    check('no_unresolved_hit_metrics',all(v['unknown']==0 for g in summary['groups'].values() for v in g['hits'].values()))
    check('primary_denominators_98',all(v['n']==98 for g in summary['groups'].values() for v in g['hits'].values()))
    check('rr5_ceiling_respected',summary['groups']['RR5']['hits']['1']['hits']<=summary['groups']['Baseline']['hits']['5']['hits'])
    check('rr10_ceiling_respected',summary['groups']['RR10']['hits']['1']['hits']<=summary['groups']['Baseline']['hits']['10']['hits'])
    reused={(r['query_id'],r['file']):r for r in read(HERE/'scoring_inputs/reused_support.json')}
    fresh={}
    for p in (HERE/'support_reviews').glob('*.json'):
        r=read(p)
        if 'job' in r: fresh[r['job']['query_id'],r['job']['file']]=r
    adjudications={}
    ap=HERE/'support_reviews/adjudications.jsonl'
    if ap.exists():
        for line in ap.read_text(encoding='utf-8').splitlines():
            r=json.loads(line); adjudications[r['query_id'],r['file']]=r
    enough=True
    for group,records in completed.items():
        for qid,r in records.items():
            s=standards[qid]
            if s['scope']!='single_document' or not r['references']: continue
            name=r['references'][0]['file']
            if name in s['known_supporting_sources']: continue
            key=(qid,name)
            if key in adjudications: continue
            if key in reused:
                v=reused[key]; enough &= v['adjudicated'] or v['review_count']>=2
            else:
                v=fresh.get(key); enough &= bool(v and v['support'] is not None and len(v['reviews'])>=2)
    check('first_position_exceptions_sufficiently_checked',enough)
    jobs=read(HERE/'review_inputs/jobs.json')
    check('all_required_new_source_jobs_completed',set(fresh)=={(j['query_id'],j['file']) for j in jobs})
    check('new_positive_decisions_grounded',all(len(r['reviews'])==2 and all(v.get('coverage')=='full' and v.get('identity')=='correct' and v.get('all_quotes_grounded') for v in r['reviews']) for r in fresh.values() if r['support'] is True))
    source_calls=[json.loads(line) for p in (HERE/'support_reviews').glob('calls*.jsonl') for line in p.read_text(encoding='utf-8').splitlines()]
    check('source_check_runtime_verified',all(c.get('requested_model')==c.get('response_model')==settings['model'] and c.get('outbound_http_models')==[settings['model']] and c.get('phase')=='support_review' for c in source_calls if c['status']=='ok'))
    preflight=[json.loads(line) for line in (HERE/'preflight_calls.jsonl').read_text(encoding='utf-8').splitlines()]
    check('preflight_runtime_verified',bool(preflight) and all(c.get('requested_model')==c.get('response_model')==settings['model'] and c.get('outbound_http_models')==[settings['model']] for c in preflight if c['status']=='ok'))
    result=dict(checks=len(checks),passed=sum(c['passed'] for c in checks),all_passed=all(c['passed'] for c in checks),details=checks)
    save(HERE/'reports/validation.json',result)
    print(json.dumps(result,indent=2))
    if not result['all_passed']: raise SystemExit(1)

if __name__=='__main__': main()
