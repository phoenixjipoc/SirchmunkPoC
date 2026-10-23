"""Validate completeness, frozen artifacts, runtime identity and score denominators."""
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    config=read(HERE/'inputs/config.json')
    queries=read(HERE/'inputs/queries.json')
    standards=read(HERE/'inputs/standards.json')
    preflight=read(HERE/'results/basic120/preflight.json')
    complete=read(HERE/'results/basic120/complete.json')
    results=[read(p) for p in (HERE/'results/basic120/queries').glob('*.json')]
    calls=[json.loads(line) for p in sorted((HERE/'results/basic120').glob('calls*.jsonl')) for line in p.read_text(encoding='utf-8').splitlines()]
    successful=[c for c in calls if c['status']=='ok']
    corpus=read(HERE/'inputs/corpus.json')
    checks={}
    checks['all_120_unique_queries']=len(results)==len(queries)==complete['questions']==120 and {r['query_id'] for r in results}=={q['id'] for q in queries}
    checks['all_81_original_hashes_match']=len(corpus)==81 and all(digest(HERE.parent/'poc_docs/S'/f['file'])==f['sha256'] for f in corpus)
    checks['frozen_semantic_inputs_match']=all(digest(HERE/'inputs'/name)==h for name,h in read(HERE/'inputs/freeze_hashes.json').items())
    checks['benchmark_code_matches']=all(digest(HERE/name)==h for name,h in preflight['code_hashes'].items())
    checks['benchmark_inputs_match']=all(digest(HERE/'inputs'/name)==h for name,h in preflight['input_hashes'].items())
    checks['upstream_source_snapshot_matches']=all(digest(HERE/'source_snapshot'/name)==h for name,h in preflight['source_hashes'].items())
    checks['all_successful_runtime_identifiers_match']=bool(successful) and all(c.get('requested_model')==c.get('response_model')==config['model'] and c.get('outbound_http_models')==[config['model']] and c.get('model_match') for c in successful)
    checks['failed_calls_remain_recorded']=all(c.get('error_type') and c.get('requested_model')==config['model'] for c in calls if c['status']!='ok')
    checks['only_discovery_calls']=set(c['phase'] for c in calls)<={'keywords','directory'}
    checks['no_answer_sampling_or_cluster_flags']=all(r.get('answer_generated') is False and r.get('evidence_sampling') is False and r.get('cluster_used') is False for r in results)
    checks['rank_order_and_unique_sources']=all([x['rank'] for x in r['references']]==list(range(1,len(r['references'])+1)) and len(r['references'])==len({x['file'] for x in r['references']})<=10 for r in results)
    checks['returned_sources_belong_to_corpus']=all(ref['file'] in {f['file'] for f in corpus} for r in results for ref in r['references'])
    checks['returned_order_is_native_prefix']=all([x['path'] for x in r['references']]==r.get('merged_files',[])[:10] for r in results)
    checks['raw_files_contain_no_final_answer_field']=all('answer' not in r for r in results)
    checks['preflight_confirmed']=preflight['model_preflight_passed'] and preflight['corpus_hashes_match'] and preflight['scan_files']==81
    parser=read(HERE/'results/basic120/parser_validation.json')
    checks['parser_outcomes_recorded_for_all_originals']=len(parser['files'])==81 and {x['file'] for x in parser['files']}=={x['file'] for x in corpus}
    summary=read(HERE/'reports/basic120/summary.json')
    checks['correct_denominators']=summary['questions']==120 and summary['single_document']==98 and summary['cross_document']==13 and summary['unanswerable']==9 and summary['pairs']['n']==15
    checks['cutoff_scores_monotonic']=summary['top_k']['1']['hits']<=summary['top_k']['5']['hits']<=summary['top_k']['10']['hits']
    jobs=read(HERE/'review_inputs/jobs.json')
    decisions=[read(p) for p in (HERE/'support_reviews').glob('*.json')]
    by_id={d['job']['id']:d for d in decisions}
    checks['all_unlisted_document_jobs_reviewed']={j['id'] for j in jobs}=={d['job']['id'] for d in decisions}
    checks['additional_positives_have_two_grounded_checks']=all(len(d['reviews'])==2 and all(r.get('coverage')=='full' and r.get('all_quotes_grounded') for r in d['reviews']) for d in decisions if d['support'] is True)
    checks['unlisted_first_results_have_two_completed_checks']=all(len(by_id[j['id']]['reviews'])==2 and all('error' not in v for v in by_id[j['id']]['reviews']) for j in jobs if j['second_check_required'])
    adjudications=[json.loads(line) for line in (HERE/'support_reviews/adjudications.jsonl').read_text(encoding='utf-8').splitlines()]
    adjudicated={a['job_id'] for a in adjudications}
    checks['quotation_discrepancies_adjudicated']=all(d['job']['id'] in adjudicated for d in decisions if any(v.get('all_quotes_grounded') is False for v in d['reviews']))
    checks['adjudication_sources_match']=all(digest(HERE/'review_inputs/texts'/(a['text_hash']+'.txt'))==a['text_hash'] and (not a.get('visual_source') or digest(HERE.parent/a['visual_source']['path'])==a['visual_source']['sha256']) for a in adjudications)
    review_calls=[json.loads(line) for p in (HERE/'support_reviews').glob('calls_*.jsonl') for line in p.read_text(encoding='utf-8').splitlines()]
    checks['successful_review_runtime_identifiers_match']=all(c.get('requested_model')==c.get('response_model')==config['model'] and c.get('outbound_http_models')==[config['model']] and c.get('phase')=='support_review' for c in review_calls if c['status']=='ok')
    if complete.get('retained_query_ids'):
        prior=HERE/'attempts/network_interruption/results/queries'
        checks['previously_completed_results_unchanged']=all(digest(prior/(qid+'.json'))==digest(HERE/'results/basic120/queries'/(qid+'.json')) for qid in complete['retained_query_ids'])
        checks['recovery_wrapper_hash_matches']=digest(HERE/'resume.py')==complete['recovery_script_sha256']
    validation=dict(passed=all(checks.values()),checks=checks,counts=dict(questions=len(results),retrieval_calls=len(calls),document_reviews=len(decisions),review_calls=len(review_calls)),
                    offline_checks=['runtime mismatch stop','missing runtime identifier stop','native order and deduplication','timestamp serialization','six metric-order/unknown-bound assertions'])
    (HERE/'reports/basic120/validation.json').write_text(json.dumps(validation,indent=2),encoding='utf-8')
    print(json.dumps(validation,indent=2))
    if not validation['passed']:
        raise SystemExit('Validation failed; see individual checks')


if __name__=='__main__':
    main()
