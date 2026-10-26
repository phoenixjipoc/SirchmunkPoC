"""Write the fresh before/after retrieval report."""
import csv
import json
from common import HERE,read,save

def main():
    s=read(HERE/'reports/summary.json');b=s['groups']['Baseline'];r=s['groups']['RR10']
    rows=list(csv.DictReader((HERE/'reports/questions.csv').open(encoding='utf-8',newline='')))
    standards={x['id']:x for x in read(HERE/'scoring_inputs/standards.json')}
    misses=[]
    for row in rows:
        if row['group']!='RR10' or row['scope']!='single_document' or row['hit_at_1']!='False':continue
        base=read(HERE/'baseline'/(row['id']+'.json'))
        ranked=read(HERE/'runs/RR10/queries'/(row['id']+'.json'))
        allfiles=[x.rsplit('/',1)[-1] for x in base.get('merged_files',[])]
        known=next((i+1 for i,f in enumerate(allfiles) if f in standards[row['id']]['known_supporting_sources']),0)
        if row['hit_at_10']=='True' and ranked['status']=='fallback_original':reason='technical_rerank_fallback'
        elif row['hit_at_10']=='True':reason='support_present_but_not_first'
        elif base['status']=='technical_failure':reason='technical_retrieval_failure'
        elif not base['references']:reason='empty_retrieval'
        elif known>10:reason='verified_source_beyond_cutoff'
        else:reason='verified_source_absent_from_candidates'
        misses.append(dict(id=row['id'],type=row['type'],reason=reason,known_candidate_rank=known or '',first_supported_rank=row['first_supported_rank'],top1_file=row['top1_file']))
    from analyze import csvout
    csvout('misses',misses)
    lines=['# Fresh Top-10 retrieval and reranking: batch 1','',
        'A single new retrieval pass searched the same 81 original documents for all 120 questions. Reranking then reordered each newly returned list of at most ten candidates. Historical candidate lists were not reused.','',
        '## Results','',
        'Primary measures use 98 single-document questions. A hit requires complete supporting facts for the correct identity, version and conditions.','']
    for name,v in [('Fresh retrieval',b),('After Top-10 reranking',r)]:
        h=v['hits'];lines.append(f"- {name}: Hit@1 **{h['1']['lower_pct']:.2f}% ({h['1']['hits']}/98)**; Hit@5 {h['5']['lower_pct']:.2f}% ({h['5']['hits']}/98); Hit@10 {h['10']['lower_pct']:.2f}% ({h['10']['hits']}/98); MRR@10 {v['mrr10_lower']:.4f}.")
    m=s['matched']['Baseline->RR10']
    lines+=['',f"Reranking adds {m['gains']} first-position hits and loses {m['losses']}, a net change of {r['hits']['1']['lower_pct']-b['hits']['1']['lower_pct']:+.2f} percentage points. Candidate membership and Hit@10 stay unchanged for every question.",'',
        '## Remaining misses','']
    from collections import Counter
    for reason,count in sorted(Counter(x['reason'] for x in misses).items()):lines.append(f'- {reason}: {count}.')
    lines+=['','Candidate-absence categories refer to audited sources; files outside the returned ten were not exhaustively assessed. See [miss details](misses.csv).','',
        'Of the 22 remaining first-position misses, 20 have no fully supporting file in the returned ten. CONS-07 has a supporting file at rank 3 after reranking. CONS-08 retained its original rank 5 after three connection errors; it is a technical fallback, not a completed ranking decision.','',
        '## Similar questions and other cases','']
    for name,v in [('Fresh retrieval',b),('Reranked',r)]:
        lines.append(f"- {name}: both questions hit first in {v['pairs_both']['1']}/15 pairs; an opposite question's exclusive source ranks incorrectly first on {v['opposite_first']}/30 paired queries.")
        for k in [5,10]:
            c=v['combinations'][str(k)];lines.append(f"- {name}, first {k}: required-source sets complete for {c['complete']}/12 questions, mean required-source coverage {100*c['mean_coverage']:.2f}%; thematic example coverage {v['thematic'][str(k)]}/6.")
    lines+=['','The nine negative cases report suggestions without an answerability or refusal score.','',
        '## Question types','']
    for name,v in [('Fresh retrieval',b),('Reranked',r)]:
        lines.append('- '+name+': '+'; '.join(f"{t} {h['1']['hits']}/{h['1']['n']}" for t,h in v['by_type'].items())+'.')
    lines+=['','## Execution and usage','']
    for name,v in [('Fresh retrieval',b),('Reranking stage',r)]:
        t=v['task_latency'];lines.append(f"- {name}: {v['questions']} tasks; statuses {v['statuses']}; {v['calls']} requests, {v['call_errors']} request errors and {v['tokens']:,} reported tokens. Per-task median {t['median_s']:.3f}s and p95 {t['p95_s']:.3f}s.")
    sc=s['source_checks'];pc=s['preflight']
    recovery=[read(p) for p in sorted((HERE/'recovery').glob('*.json'))]
    lines+=['',f"Source checking was separate: {sc['calls']} requests, {sc['tokens']:,} tokens and {sc['jobs']['jobs']} new or upgraded associations; {sc['jobs']['reused']} compatible decisions reused. Preflight used {pc['calls']} requests and {pc['tokens']} reported tokens.",'',
        'Two checks contained unmatched quotation fragments. Inspection of the saved source text confirmed both negative decisions; exact quotations and offsets are saved in support_reviews/adjudications.jsonl. No primary score remains unresolved.','',
        'Stage timings exclude metadata scanning, parsing warmup, source checking and downtime. P95 uses the nearest-rank method. Ranking tasks with zero or one candidate have no remote request. Paired total latency is the retrieval time plus its reranking time; the reranking stage alone is not a replacement for retrieval cost.','',
        f"Transport interruptions required {len(recovery)} checkpointed resumes. The checkpoints protected {', '.join(str(x['completed']) for x in recovery)} completed results respectively. Only unfinished tasks resumed; completed results and settings were retained. Failed attempts remain in the call and attempt records.",'',
        '## Configuration and limits','',
        'Native retrieval retained the twenty-file directory sample, fresh keyword extraction and search, keyword-first merge and ten-file cutoff. A new directory snapshot and isolated parsing cache were created. Reranking used identical filenames, titles, keywords and previews capped at 800 characters, with fixed shuffled presentation and hidden original ranks. Runtime identifiers were verified on requests and responses.','',
        'The first native result was saved successfully, but copying its in-memory log into the batch record failed on a datetime value. A serialization-only repair preserved that completed result without another request. Original code, changed hashes and the recovered result are recorded in execution_repair/.','',
        'The native legacy DOC parser remains limited: a warmup binary-match message is not readable document text. No parser repair or expanded directory budget was applied. No final answers, evidence sampling or knowledge clusters were produced.','',
        'One exposed batch measures the paired change for its own candidates; it does not establish stability or unseen performance. Fresh candidate membership can differ from earlier runs. Source checks and ranking are separate, and any scoring uncertainty must remain explicit.','',
        '## Files','',
        '- [Plan](../PLAN.md), [settings](../settings.json), [configuration](../inputs/config.json) and [execution repair](../execution_repair/revision.json).',
        '- [All 240 scores](questions.csv), [references](references.csv), [paired changes](transitions.csv) and [remaining misses](misses.csv).',
        '- [Similar pairs](pairs.csv), [combined sources](cross_document.csv), [negative cases](unanswerable.csv) and [document averages](by_document.csv).',
        '- [Summary](summary.json), [validation](validation.json) and [source-check manifest](../review_inputs/manifest.json).','']
    (HERE/'reports/REPORT.md').write_text('\n'.join(lines),encoding='utf-8')

if __name__=='__main__':main()
