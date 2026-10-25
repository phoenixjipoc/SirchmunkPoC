"""Validate isolation, source identity, completeness and score invariants."""
import hashlib
import json
from pathlib import Path
from prepare_support import HERE,BASE,read,save,results


def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    checks=[]
    def check(name,condition,detail=None):
        checks.append(dict(name=name,passed=bool(condition),detail=detail))
    freeze=read(HERE/'freeze.json')
    check('retrieval_code_and_inputs_unchanged',all(digest(HERE/n)==v for n,v in freeze['files'].items()))
    for part in ['parser','scoring','transport','parser_correction']:
        f=read(HERE/(part+'_freeze.json'))
        check(part+'_code_unchanged',all(digest(HERE/n)==v for n,v in f['files'].items()))
    questions=read(BASE/'inputs/queries.json'); ids={q['id'] for q in questions}
    check('same_120_question_inputs',len(ids)==120 and digest(BASE/'inputs/queries.json')==digest(HERE/'inputs/queries.json'))
    check('baseline_records_byte_identical',all(digest(p)==digest(BASE/'results/basic120/queries'/p.name) for p in (HERE/'baseline').glob('*.json')))
    recovery=HERE/'recovery_1.json'
    if recovery.exists():
        check('completed_R2_results_unchanged_after_recovery',all(digest(HERE/'runs/R2/queries'/(qid+'.json'))==h for qid,h in read(recovery)['retained_query_hashes'].items()))
    allowed={r['file'] for r in read(BASE/'inputs/corpus.json')}
    groups=results()
    for group,rows in groups.items():
        check(group+'_exact_120_ids',set(rows)==ids)
        check(group+'_ordered_unique_references',all(
            [x['rank'] for x in r['references']]==list(range(1,len(r['references'])+1)) and
            len({x['file'] for x in r['references']})==len(r['references'])<=10 and
            all(x['file'] in allowed for x in r['references']) for r in rows.values()))
        check(group+'_no_answer_sampling_cluster',all(r.get('answer_generated') is False and r.get('evidence_sampling') is False and r.get('cluster_used') is False for r in rows.values()))
        if group in {'R2','R3','S','D'}:
            calls=[json.loads(line) for p in (HERE/'runs'/group).glob('calls*.jsonl') for line in p.read_text(encoding='utf-8').splitlines()]
            good=[c for c in calls if c.get('status')=='ok']
            check(group+'_model_identity',bool(good) and all(c['requested_model']==c['response_model']=='gpt-6-sol' and c.get('outbound_http_models')==['gpt-6-sol'] for c in good))
            permitted={'preflight','keywords','directory'} if group in {'R2','R3'} else {'preflight','rerank' if group=='S' else 'directory'}
            check(group+'_allowed_phases',all(c['phase'] in permitted for c in calls))
            check(group+'_valid_result_not_retried',all(
                sum(read(p)['status'] in {'ok','empty_retrieval'} for p in (HERE/'runs'/group/'attempts'/qid).glob('*.json'))==1
                for qid,r in rows.items() if r['status'] in {'ok','empty_retrieval'}))
    check('S_exact_same_candidate_sets',all(
        {r['file'] for r in groups['S'][qid]['references']}=={r['file'] for r in groups['R1'][qid]['references']}
        for qid in ids if groups['S'][qid]['status'] in {'ok','empty_retrieval'}))
    check('S_prompt_has_no_gold_fields',all(
        set(json.loads(r['ranking_prompt']))=={'question','candidates'} and
        [c['filename'] for c in json.loads(r['ranking_prompt'])['candidates']]==sorted(x['file'] for x in r['references'])
        for r in groups['S'].values() if 'ranking_prompt' in r))
    check('D_keyword_results_frozen',all(groups['D'][qid].get('keyword_files')==groups['R1'][qid].get('keyword_files') for qid in ids if groups['D'][qid]['status']=='ok'))
    check('D_prompt_contains_all_81_files',all(all(name in r.get('directory_prompt','') for name in allowed) for r in groups['D'].values() if r['status']=='ok'))
    check('P_P0_same_terms_and_directory',all(
        groups[g][qid]['keyword_terms']==groups['R1'][qid]['keyword_terms'] and groups[g][qid]['directory_files']==groups['R1'][qid]['directory_files']
        for g in ['P','P0'] for qid in ids))
    parser=read(HERE/'parser_validation.json')
    check('parser_checks_cover_both_81_file_sets',all({r['file'] for r in parser if r['group']==g}==allowed for g in ['P','P0']))
    check('legacy_doc_readable_with_adapter',all(r['readable_text'] and r['byte_matches']==0 for r in parser if r['group']=='P' and r['file'].endswith('.doc')))
    complete=read(HERE/'parser_complete.json')
    check('parser_live_async_hook_and_sort_confirmed',complete.get('corrected_async_hook') and complete.get('file_order')=='path in both arms' and complete.get('driver_sha256')==digest(HERE/'parser_replay_corrected.py'))
    check('parser_integration_smoke_passed',read(HERE/'parser_correction_smoke.json')['passed'])
    trace=[json.loads(l) for l in (HERE/'parser_async_trace.jsonl').read_text(encoding='utf-8').splitlines()]
    live=[r for r in trace if r['stage']=='corrected_replay']
    check('parser_actual_invocation_flags',bool(live) and {r['variant'] for r in live}=={'P0','P'} and all('--sort=path' in r['args'] and any(a.startswith('--rga-config-file=') for a in r['args'])==(r['variant']=='P') for r in live))
    stage=read(HERE/'reports/stage_diagnostics.json')['summary']['parser']
    check('parser_nonlegacy_order_and_membership_controlled',stage['nonlegacy_order_changes']==stage['nonlegacy_set_changes']==0)
    check('initial_invalid_parser_results_preserved',all(len(list((HERE/'parser_initial_invalid/runs'/g/'queries').glob('*.json')))==120 for g in ['P0','P']))
    standards=read(BASE/'inputs/standards.json')
    original_standards=read(HERE/'scoring_inputs/baseline_input_hashes.json')
    check('scoring_inputs_equal_published_baseline',all(digest(BASE.parent/name)==h for name,h in original_standards['files'].items()))
    check('scope_denominators',sum(r['scope']=='single_document' for r in standards)==98 and sum(r['scope']=='required_combination' for r in standards)==12 and sum(r['scope']=='thematic_examples' for r in standards)==1 and sum(r['scope']=='negative' for r in standards)==9)
    anchors=read(HERE/'scoring_inputs/anchor_validation.json')
    adjudicated=read(HERE/'scoring_inputs/anchor_adjudications.json')
    check('all_360_anchors_supported_by_text_or_page',anchors['matched_anchors']+sum(a['anchor_supported'] for a in adjudicated)==anchors['quoted_anchors']==360)
    check('anchor_page_images_unchanged',all(digest(BASE.parent/a['image'])==a['image_sha256'] for a in adjudicated))
    jobs=read(HERE/'review_inputs/jobs.json')
    reviews=[read(HERE/'support_reviews'/(j['id']+'.json')) for j in jobs if (HERE/'support_reviews'/(j['id']+'.json')).exists()]
    check('all_new_checks_completed',len(reviews)==len(jobs))
    review_by_id={r['job']['id']:r for r in reviews}
    check('first_position_checks_have_two_votes',all(j['id'] in review_by_id and len(review_by_id[j['id']]['reviews'])>=2 for j in jobs if j['second_check_required']))
    check('new_positive_support_requires_two_grounded_votes',all(len(r['reviews'])==2 and all(v['coverage']=='full' and v.get('all_quotes_grounded') and v.get('identity')=='correct' for v in r['reviews']) for r in reviews if r.get('support') is True))
    check('review_text_hashes_match',all(digest(HERE/'review_inputs/texts'/(j['text_hash']+'.txt'))==j['text_hash'] for j in jobs))
    source_calls=[json.loads(line) for p in (HERE/'support_reviews').glob('calls*.jsonl') for line in p.read_text(encoding='utf-8').splitlines()]
    source_success=[c for c in source_calls if c.get('status')=='ok']
    check('source_check_model_identity',all(c['requested_model']==c['response_model']=='gpt-6-sol' and c.get('outbound_http_models')==['gpt-6-sol'] for c in source_success))
    check('source_checks_only_use_support_phase',all(c['phase']=='support_review' for c in source_calls))
    adjudication_file=HERE/'support_reviews/adjudications.jsonl'
    adjudications=[json.loads(l) for l in adjudication_file.read_text(encoding='utf-8').splitlines()] if adjudication_file.exists() else []
    from prepare_support import AUDIT,norm
    def grounded(a):
        source=AUDIT/'source_text'/(a['file']+'.txt')
        text=norm(source.read_text(encoding='utf-8-sig'))
        if digest(source)!=a['source_text_sha256'] or hashlib.sha256(text.encode()).hexdigest()!=a['text_hash']: return False
        if a['method']=='direct_rendered_page_review':
            return bool(a.get('images')) and bool(a.get('visual_quotes')) and all(digest(HERE/i['path'])==i['sha256'] for i in a['images'])
        return bool(a.get('quotes')) and all(text[q['start']:q['end']]==q['quote'] for q in a['quotes'])
    check('adjudication_evidence_grounded',all(grounded(a) for a in adjudications))
    checked={(a['query_id'],a['file']) for a in adjudications}
    check('unmatched_review_quotes_adjudicated',all((r['job']['query_id'],r['job']['file']) in checked for r in reviews if any(not v.get('all_quotes_grounded',False) for v in r['reviews'])))
    summary=read(HERE/'reports/summary.json')
    check('hit_cutoffs_monotone',all(s['hits']['1']['hits']<=s['hits']['5']['hits']<=s['hits']['10']['hits'] for s in summary['groups'].values()))
    check('MRR_bounds_valid',all(0<=s['mrr10_lower']<=s['mrr10_upper']<=1 for s in summary['groups'].values()))
    validS=all(r['status'] in {'ok','empty_retrieval'} for r in groups['S'].values())
    check('S_top10_invariant_on_completed_permutations',not validS or summary['groups']['S']['hits']['10']==summary['groups']['R1']['hits']['10'])
    result=dict(passed=all(c['passed'] for c in checks),checks=checks)
    save(HERE/'reports/validation.json',result)
    print(json.dumps(dict(passed=result['passed'],checks=len(checks),failed=[r for r in checks if not r['passed']]),indent=2))
    if not result['passed']: raise SystemExit(1)


if __name__=='__main__': main()
