"""Write a concise English report from completed, auditable source scores."""
import csv
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
OUT=HERE/'reports/basic120'


def rows(name):
    return list(csv.DictReader((OUT/name).open(encoding='utf-8')))


def main():
    s=json.loads((OUT/'summary.json').read_text(encoding='utf-8'))
    questions=rows('questions.csv')
    pairs=rows('pairs.csv')
    negative=rows('unanswerable.csv')
    cross=rows('cross_document.csv')
    calls=[]
    for p in (HERE/'support_reviews').glob('calls_*.jsonl'):
        calls.extend(json.loads(line) for line in p.read_text(encoding='utf-8').splitlines())
    reviews=[json.loads(p.read_text(encoding='utf-8')) for p in (HERE/'support_reviews').glob('*.json')]
    parser=json.loads((HERE/'results/basic120/parser_validation.json').read_text(encoding='utf-8'))
    additional=[x for x in reviews if x['support'] is True]
    adjudications=[json.loads(line) for line in (HERE/'support_reviews/adjudications.jsonl').read_text(encoding='utf-8').splitlines()]
    def metric(k):
        m=s['top_k'][str(k)]
        if m['unknown']:
            return f"{m['hits']}/{m['n']} confirmed; {m['unknown']} unresolved ({m['lower_pct']:.2f}%–{m['upper_pct']:.2f}%)"
        return f"{m['hits']}/{m['n']} ({m['lower_pct']:.2f}%)"
    failure=[]
    for row in questions:
        if row['scope']!='single_document' or row['document_hit_at_1']=='True': continue
        r=json.loads((HERE/'results/basic120/queries'/(row['id']+'.json')).read_text(encoding='utf-8'))
        known=set(row['verified_sources'].split(';'))
        if row['status'] not in ['ok','empty_retrieval']: cause='execution_error'
        elif row['status']=='empty_retrieval': cause='empty_retrieval'
        elif row['document_hit_at_1']=='': cause='unresolved_support'
        elif row['document_hit_at_5']=='True': cause='support_at_ranks_2_to_5'
        elif row['document_hit_at_10']=='True': cause='support_at_ranks_6_to_10'
        elif any(Path(f).name in known for f in r.get('merged_files',[])): cause='verified_source_beyond_top10'
        else: cause='verified_source_absent_from_candidates'
        failure.append(dict(id=row['id'],type=row['type'],top1_file=row['top1_file'],
                            verified_sources=row['verified_sources'],category=cause))
    with (OUT/'failures.csv').open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=['id','type','top1_file','verified_sources','category']); w.writeheader(); w.writerows(failure)
    categories={c:sum(r['category']==c for r in failure) for c in sorted({r['category'] for r in failure})}
    text=[
        '# Basic document retrieval results',
        '',
        f"**Document Hit@1: {metric(1)}.** Hit@5: {metric(5)}. Hit@10: {metric(10)}.",
        '',
        'One pass covered all 120 questions against 81 original documents. Each query returned up to ten ordered files. The three cutoffs use the same results; they are not separate runs. No final answers, evidence summaries or knowledge clusters were produced.',
        '',
        '## What the result means',
        '',
        'The primary denominator is the 98 single-document questions. A hit requires a document containing the mandatory facts for the correct issuer, edition and conditions. Verified sources use the completed source audit; other returned files receive separate checks against their original-derived text. This measures document retrieval, not whether a selected excerpt or generated answer is sufficient.',
        '',
        f"The twelve source-combination questions, one thematic question and nine unanswerable questions are separate. Execution statuses: {', '.join(f'{k}={v}' for k,v in sorted(s['statuses'].items()))}. Errors remain in denominators.",
        '',
        '## Single-document categories',
        '',
    ]
    for t,metrics in s['by_type'].items():
        vals=[]
        for k in [1,5,10]:
            m=metrics[str(k)]; vals.append(f"Top-{k}: {m['hits']}/{m['n']} ({m['lower_pct']:.2f}%)"+(f", {m['unknown']} unresolved" if m['unknown'] else ''))
        text.append(f"- {t}: {'; '.join(vals)}.")
    text+=['','## Similar questions','',
           f"The fifteen pairs are included in the 120 questions. Both sides found supporting sources at rank one in {s['pairs']['both_correct']['1']}/15 pairs, within five in {s['pairs']['both_correct']['5']}/15, and within ten in {s['pairs']['both_correct']['10']}/15. The opposite question's exclusive source appeared incorrectly first in {s['pairs']['opposite_source_first']} of the thirty paired queries.",
           '',
           'An opposite source appearing later is recorded as a distractor, not automatically an error. A shared file is not automatically confusion. See [pair details](pairs.csv).',
           '', '## Cross-document coverage','']
    for k in [1,5,10]:
        m=s['required_combinations'][str(k)]
        text.append(f"- Top-{k}: complete verified source sets for {m['complete']}/12 questions; mean source-set coverage {m['mean_source_coverage']*100:.2f}%.")
    theme=next(r for r in cross if r['scope']=='thematic_examples')
    text+=['',f"For the thematic DDQ question, Top-10 found {theme['found_at_10']}/{theme['required_count']} verified example sources. Its examples are not an exhaustive relevance set. Source-set coverage is not proof that every possible minimum evidence combination has been enumerated. See [coverage details](cross_document.csv).",'',
           '## Unanswerable questions','',
           f"{sum(int(r['returned_count'])>0 for r in negative)}/9 negative questions returned documents. Those suggestions can be background material. The retriever does not assert an answer or make an answerability decision, so this is neither a false-answer rate nor a correct-refusal rate. The prior absence findings and returned files are preserved in [unanswerable cases](unanswerable.csv).",'',
           '## Failure analysis','']
    labels={'empty_retrieval':'No files returned','support_at_ranks_2_to_5':'Supporting file ranked 2–5',
            'support_at_ranks_6_to_10':'Supporting file ranked 6–10',
            'verified_source_absent_from_candidates':'Verified source absent from discovered candidates',
            'verified_source_beyond_top10':'Verified source found beyond the ten-file cutoff',
            'execution_error':'Execution errors','unresolved_support':'Unresolved source support'}
    for category,count in categories.items():
        text.append(f"- {labels[category]}: {count} questions.")
    imrf=next(r for r in questions if r['id']=='INV-12')
    outcomes=[{'True':'hit','False':'miss','':'unresolved'}[imrf[f'document_hit_at_{k}']] for k in [1,5,10]]
    text+=['',f"INV-12 illustrates the distinction between document similarity and support. Its first result was `{imrf['top1_file']}`; the verified source is `{imrf['verified_sources']}`. The question asks about investment-manager evaluation, so consulting requirements are not interchangeable. Its Top-1/5/10 outcomes are {' / '.join(outcomes)}.",
           '', 'The installed merge places keyword hits before high-relevance directory suggestions. It does not globally rerank the combined list. Directory selection also samples twenty of the 81 files. These properties can explain poor first-position ordering or incomplete candidate discovery; this run does not isolate their individual causal effects.', '',
           '## Runtime and source checks','',
           f"All {s['runtime']['calls']} retrieval call attempts were recorded: {s['runtime']['successful_calls']} successful responses and {s['runtime']['errors']} errors. Identity checks for successful responses {'passed' if s['runtime']['all_successful_http_and_response_models_match'] else 'failed'}. There were {s['runtime']['phases']['keywords']} keyword requests and {s['runtime']['phases']['directory']} directory requests, including failed and recovered attempts. Exact runtime identifiers, source hashes and image digest are in the [runtime records](../../results/basic120/preflight.json) and [environment record](../../runtime_environment.json).",'',
           f"A connection interruption required technical recovery of {s['recovery']['recovered_queries']} queries. The {s['recovery']['retained_queries']} previously completed results were retained unchanged. Failed attempts remain in the archive and call totals; the baseline contains one completed result per question, not one network attempt per question. No semantic failure was retried to improve its score.", '',
           f"Median completed-query time was {s['latency']['median_s']:.2f} seconds. The sum of completed-query times was {s['latency']['total_query_s']/60:.2f} minutes. Reported retrieval usage was {s['runtime']['tokens']['prompt_tokens']:,} input and {s['runtime']['tokens']['completion_tokens']:,} output tokens; failed calls without usage data cannot be assigned a token cost. Cache warmup, interruption time and source verification are separate. Concurrent source checks may affect timing, so latency is an observation rather than an isolated performance comparison.", '',
           f"Separate checks covered {len(reviews)} unlisted returned documents using {len(calls)} requests. They confirmed {len(additional)} additional supporting source associations. Reported verification tokens: {sum(c.get('usage',{}).get('total_tokens',0) or 0 for c in calls):,}. Every proposed additional positive and unlisted first result receives two separate requests; the two checks use the same configured service and are not independent proof. {len(adjudications)} quotation-format discrepancies were resolved using exact source passages or a saved original-page image; see [adjudications](../../support_reviews/adjudications.jsonl).", '',
           f"Parser validation found readable keyword text in {parser['text_files']}/81 originals. The legacy INREV DOC returned byte matches rather than normal text. It is a verified source for cross-document question XD-16; it remained in the corpus and was not converted or excluded. This limitation is distinct from whether the original file itself contains the required facts. See [parser validation](../../results/basic120/parser_validation.json).", '',
           '## Limits and artifacts','',
           'This is a single-run baseline. It does not measure repeated-run stability, answer generation, cluster reuse, excerpt quality or calibrated refusal. No product acceptance threshold is inferred. Earlier aborted starts are archived and excluded.', '',
           '- [All 120 question scores](questions.csv)',
           '- [Ordered references and support decisions](references.csv)',
           '- [First-position failures](failures.csv)',
           '- [Machine-readable summary](summary.json)',
           '- [Artifact validation](validation.json)',
           '- [Plan](../../PLAN.md) and [reproduction guide](../../README.md)',
           '- [Execution record](../../EXECUTION.md)',
           '']
    (OUT/'REPORT.md').write_text('\n'.join(text),encoding='utf-8')
    print('Report written.')


if __name__=='__main__':
    main()
