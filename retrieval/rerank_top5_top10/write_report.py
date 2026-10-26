"""Publish concise English results from computed scores."""
import csv
from common import HERE, read

def main():
    summary=read(HERE/'reports/summary.json')
    groups=summary['groups']
    transitions=list(csv.DictReader((HERE/'reports/transitions.csv').open(encoding='utf-8',newline='')))
    lines=['# Top-five and top-ten reranking results','',
        'One pass per arm used all 120 questions and 81 original documents. Both new arms reused the same R1 retrieval lists. RR5 reordered positions 1-5 and preserved positions 6-10; RR10 reordered positions 1-10. No new discovery, final answers or knowledge clusters were produced.','',
        '## Document support','',
        'The primary denominator is 98 single-document questions. A qualifying document contains every mandatory fact for the correct organization, edition and conditions.','']
    for group,v in groups.items():
        h=v['hits']
        lines.append(f"- {group}: Hit@1 **{h['1']['lower_pct']:.2f}% ({h['1']['hits']}/98)**; Hit@5 {h['5']['lower_pct']:.2f}% ({h['5']['hits']}/98); Hit@10 {h['10']['lower_pct']:.2f}% ({h['10']['hits']}/98). MRR@10 {v['mrr10_lower']:.4f}.")
    lines+=['','## Paired changes','']
    for name,v in summary['matched'].items():
        before,after=name.split('->')
        delta=groups[after]['hits']['1']['lower_pct']-groups[before]['hits']['1']['lower_pct']
        lines.append(f"- {before} to {after}: {v['gains']} first-position gains, {v['losses']} losses; net change {delta:+.2f} percentage points.")
    lines+=['',
        'Hit@10 is unchanged for every question because candidate membership is fixed. RR5 Hit@5 is also unchanged. Reranking cannot recover a source outside its candidate pool.','',
        '## Question types and similar pairs','']
    for group,v in groups.items():
        types='; '.join(f"{t}: {data['1']['hits']}/{data['1']['n']}" for t,data in v['by_type'].items())
        lines.append(f"- {group}: first-position hits by type — {types}. Both questions hit first in {v['pairs_both']['1']}/15 similar-question pairs; an opposite question's exclusive source ranks incorrectly first on {v['opposite_first']}/30 paired queries.")
    lines+=['','## Other 22 questions','']
    for group,v in groups.items():
        cs=v['combinations']
        lines.append(f"- {group}: complete required-source sets at five {cs['5']['complete']}/12 and at ten {cs['10']['complete']}/12; mean source coverage at five {100*cs['5']['mean_coverage']:.2f}% and at ten {100*cs['10']['mean_coverage']:.2f}%. The thematic question retrieves {v['thematic']['5']}/6 listed example sources at five and {v['thematic']['10']}/6 at ten.")
    lines+=['','The nine negative cases retain document suggestions only. No refusal accuracy or false-answer rate is inferred.','',
        '## Execution and cost','']
    for group in ['RR5','RR10']:
        v=groups[group]; lat=v['request_latency']
        lines.append(f"- {group}: {v['questions']} completed tasks; statuses {v['statuses']}. Ranking requests {v['calls']}, request errors {v['call_errors']}, reported tokens {v['tokens']:,} ({v['prompt_tokens']:,} input, {v['completion_tokens']:,} output). Request median {lat['median_s']:.3f}s, p95 {lat['p95_s']:.3f}s.")
    pc=summary['preflight']; sc=summary['source_checks']; m=sc['jobs']
    lines += ['',f"Preflight: {pc['calls']} requests and {pc['tokens']:,} tokens. Separate source checks: {sc['calls']} new requests and {sc['tokens']:,} tokens, covering {m['jobs']} new or upgraded associations; {m['reused']} compatible associations reused. Existing verified positive sources retain their original audit.",'',
        'Ranking time is stage-only and excludes source checking, container startup and input preparation. P95 uses the nearest-rank percentile. Historical full-search timings are not a matched comparison. The first smoke question had one candidate and used the skip path; subsequent nontrivial tasks exercised permutation validation. Completed tasks were never repeated for a better score.','',
        'A connection interruption exhausted three attempts for RR5 XD-01. Its original order remains the reported result, with a technical-fallback flag; it remains in the 98-question denominator. The failed recovery check stopped further tasks. A later successful preflight resumed unfinished work with unchanged settings. All 97 previously completed result hashes were retained.','',
        '## Examples','']
    for comparison in ['Baseline->RR5','Baseline->RR10','RR5->RR10']:
        subset=[r for r in transitions if r['comparison']==comparison]
        for label,key in [('gain','gain'),('loss','loss')]:
            cases=[r for r in subset if r[key]=='True'][:2]
            for r in cases:
                lines.append(f"- {comparison}, {r['id']} ({label}): `{r['before_file']}` at first changes to `{r['after_file']}`. First supported rank: {r['before_rank'] or 'absent'} to {r['after_rank'] or 'absent'}.")
    lines+=['','## Interpretation and limits','',
        'These results measure reranking from filenames, titles, keywords and previews of at most 800 characters. Eight cached full-content fields were excluded. Three corpus documents have empty saved previews and therefore rely on the remaining metadata when present among candidates. Source scoring used complete original-derived text and the existing evidence audit.','',
        'Both arms received identical fields for shared documents, with a fixed hash-based presentation order and hidden original ranks. Runtime identity was checked in outgoing requests and responses. Source checks ran afterward and did not feed back into ranking.','',
        'This is an exposed benchmark with one pass per arm. It does not establish unseen performance, repeated-run stability or a product acceptance threshold. Preview truncation can hide relevant facts. More candidates can also introduce competing documents, so RR10 need not outperform RR5 on every question.','',
        '## Files','',
        '- [Plan](../PLAN.md), [settings](../settings.json) and [frozen inputs](../freeze.json).',
        '- [All 360 scores](questions.csv), [ordered references](references.csv) and [paired changes](transitions.csv).',
        '- [Similar pairs](pairs.csv), [combined sources](cross_document.csv), [negative cases](unanswerable.csv) and [document averages](by_document.csv).',
        '- [Summary](summary.json), [validation](validation.json) and [source-check jobs](../review_inputs/manifest.json).','']
    (HERE/'reports/REPORT.md').write_text('\n'.join(lines),encoding='utf-8')

if __name__=='__main__': main()
