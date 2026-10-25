"""Generate a concise English report from completed follow-up artifacts."""
import json
from pathlib import Path
from prepare_support import HERE,read,save,results


def main():
    s=read(HERE/'reports/summary.json'); groups=s['groups']; checks=read(HERE/'reports/validation.json')
    all_records=results(); all_standards=read(HERE.parent/'inputs/standards.json')
    thematic=next(q for q in all_standards if q['scope']=='thematic_examples')
    negative_ids=[q['id'] for q in all_standards if q['scope']=='negative']
    names={'R1':'Original baseline','R2':'Repeat, seed 17012','R3':'Repeat, seed 17013',
           'S':'Fixed-candidate reranking','D':'All 81 directory candidates',
           'P0':'Fixed-order keyword replay without parser repair','P':'Fixed-order keyword replay with parser repair',
           'K':'Keyword-only diagnostic','T':'Directory-only diagnostic'}
    def metric(g,k):
        r=groups[g]['hits'][str(k)]
        if r['unknown']: return f"{r['lower_pct']:.2f}%–{r['upper_pct']:.2f}% ({r['hits']}/98 confirmed; {r['unknown']} unresolved)"
        return f"{r['lower_pct']:.2f}% ({r['hits']}/98)"
    lines=['# Retrieval follow-up results','',
        'The same 120 questions and 81 raw documents were retained. There are 98 single-document questions, twelve required-source combinations, one thematic question and nine negative cases. No final answers or knowledge clusters were produced.','',
        '## Repeated runs','']
    for g in ['R1','R2','R3']:
        lines.append(f"- {g}, {names[g]}: Hit@1 {metric(g,1)}; Hit@5 {metric(g,5)}; Hit@10 {metric(g,10)}. MRR@10 {groups[g]['mrr10_lower']:.4f}.")
    st=s['stability']
    lines+=['',f"Mean Hit@1 was {st['mean_top1_pct']:.2f}%, with a {st['min_top1_pct']:.2f}%–{st['max_top1_pct']:.2f}% range. {st['all_three_hit']}/98 questions hit in all three runs; {st['all_three_miss']}/98 missed in all three; {st['correctness_changes']}/98 changed between hit and miss. The first filename changed on {st['top1_file_changes']}/98 questions. These are repeated observations of 98 questions, not 294 independent questions.",
        '', '## Controlled comparisons','']
    for g in ['S','D','P']:
        m=s['matched'][g]
        comparator='P0' if g=='P' else 'R1'
        lines.append(f"- {g}, {names[g]}: Hit@1 {metric(g,1)}; Hit@5 {metric(g,5)}; Hit@10 {metric(g,10)}. MRR@10 {groups[g]['mrr10_lower']:.4f}. First-position changes against {comparator}: gains {m['gains']}, losses {m['losses']}.")
    lines+=['',
        'S permutes the original first ten candidates using the question and frozen directory snapshot. The snapshot contains metadata/previews and cached full text for eight short documents; those cached fields are also supplied. The candidate set stays fixed; valid permutations cannot change Hit@10. D reuses the original keyword results and changes only the directory-stage candidate budget from twenty to 81. Its result remains keyword-first. These are stage-level comparisons, not new complete search runs.',
        '',f"P0: Hit@1 {metric('P0',1)}, Hit@10 {metric('P0',10)}. P and P0 replay identical frozen keyword terms and directory results on the original files. Both use fixed file-path order; P alone enables the corpus-specific legacy Word parser through the live asynchronous executor. This is a parsing diagnostic, not a proposed relevance-ranking method. Compare P with P0, not directly with R1.",
        '', 'The initial parser comparison patched an unused synchronous function. Those invalid comparison records are preserved separately. A real keyword-tool integration check passed before the corrected 120-question replay. See the [correction record](../PARSER_CORRECTION.md).',
        '', '## Examples','',
        '- INV-12: reranking moves the IMRF investment-manager RFP ahead of the similarly named consulting RFP. [S result](../runs/S/queries/INV-12.json).',
        '- CONS-07: S still puts the TMRS consulting RFP first; the qualifying OCERS document remains third. Snapshot reranking does not resolve this numeric-qualification query. [S result](../runs/S/queries/CONS-07.json).',
        '- DDQ-08: the baseline returns no file; D returns the required ILPA FAQ first. [D result](../runs/D/queries/DDQ-08.json).',
        '- SVC-07: D puts the SBCERS custody RFP ahead of the required TMRS custody RFP, moving the correct file from first to second. [D result](../runs/D/queries/SVC-07.json).',
        '', '## Similar questions and combined sources','']
    for g in ['R1','R2','R3','S','D','P0','P']:
        r=groups[g]
        lines.append(f"- {g}: both questions hit first in {r['pairs_both']['1']}/15 pairs; both hit within ten in {r['pairs_both']['10']}/15. An opposite pair's exclusive source appeared incorrectly first on {r['opposite_first']}/30 paired queries. Required-source sets were complete within ten for {r['required_combinations']['10']['complete']}/12 questions, with mean source coverage {100*r['required_combinations']['10']['mean_coverage']:.2f}%.")
    theme_counts=[]; negative_counts=[]
    for g in ['R1','R2','R3','S','D','P0','P']:
        found={r['file'] for r in all_records[g][thematic['id']]['references']} & set(thematic['required_sources'])
        theme_counts.append(f"{g} {len(found)}/{len(thematic['required_sources'])}")
        negative_counts.append(f"{g} {sum(bool(all_records[g][q]['references']) for q in negative_ids)}/9")
    lines+=['',
        f"Thematic question {thematic['id']}, listed example sources within ten: "+'; '.join(theme_counts)+'.',
        '', 'Negative queries returning one or more suggestions: '+'; '.join(negative_counts)+'.',
        '',
        'The thematic question has a non-exhaustive example-source set and is reported separately. Negative queries produce document suggestions without an answerability decision; neither refusal accuracy nor a false-answer rate is inferred.',
        '', '## Source-path diagnostics','']
    for g in ['K','T']:
        lines.append(f"- {g}, {names[g]}: Hit@1 {metric(g,1)}, Hit@10 {metric(g,10)}.")
    stage=read(HERE/'reports/stage_diagnostics.json')['summary']
    dp=stage['directory']['D']; pp=stage['parser']
    lines+=['', 'K and T replay the original path outputs. They do not rerun discovery or measure independent search latency.',
        '', 'Native keyword scoring reorders matching lines within each file, then retains the file discovery order. The harness merges keyword files before directory files; it does not perform a global relevance ranking of documents. In the archived initial parser replay, both arms used the default parser and identical keywords, yet 73/120 file orders changed while candidate membership stayed unchanged. This demonstrates an ordering source of instability separate from keyword generation and directory sampling. See the [initial diagnostics](../parser_initial_invalid/stage_diagnostics.json).',
        '',f"D included and returned ranking records for all 81 filenames on every query. High-relevance files absent from the supplied candidates occurred on {dp['queries_with_high_file_not_in_prompt']} queries. All 98 verified single-document sources occurred in the merged candidate lists; eight fell beyond the ten-file cutoff.",
        '',f"Keyword order changed on {pp['original_vs_control_order_changes']}/120 queries between R1 and P0, and on {pp['control_vs_repaired_order_changes']}/120 between P0 and P. Excluding the legacy file, P0/P order changed on {pp['nonlegacy_order_changes']}/120 and membership changed on {pp['nonlegacy_set_changes']}/120. The legacy file appeared in keyword results on {pp['legacy_discovered_control']} control queries and {pp['legacy_discovered_repaired']} repaired queries. The fixed-order comparison isolates parser effects from native file-order variation.",
        '', '## Question types and failures','']
    for g in ['R1','R2','R3','S','D','P0','P']:
        types=groups[g]['by_type']
        breakdown='; '.join(f"{t}: {v['1']['hits']}/{v['1']['n']}" for t,v in types.items())
        lines.append(f"- {g} first-position hits by type: {breakdown}. Equal-weight document average: {groups[g]['macro_document_top1_lower_pct']:.2f}%.")
    for g in ['R1','S','D','P']:
        breakdown='; '.join(f"{k}: {v}" for k,v in groups[g]['failures'].items())
        lines+=['',f"{g} outcome categories: {breakdown}."]
    lines+=['', 'Candidate absence and cutoff categories use the verified source list. Files outside the returned ten were not exhaustively assessed. A missed candidate alone does not establish a parsing or version-selection failure.',
        '', '## Measurement and source checks','',
        'Document support requires all mandatory facts for the correct issuer, version and conditions. Hit@k means at least one qualifying document appears in the first k files. MRR@10 averages the reciprocal position of the first qualifying document, assigning zero when none occurs within ten. Equal-weight document averages are reported alongside question-level scores; the 98 single-document questions cover 73 documents.',
        '',
        'Verified positives retain the completed source audit. Unlisted returned sources reuse compatible source checks or receive fresh full-text checks. Newly first-ranked unlisted sources receive two separate checks. Unresolved support remains explicit and produces score bounds. The same configured service is used for the separate checks; agreement is not independent proof.',
        '',
        'All 360 preserved evidence anchors were checked: 358 matched normalized source text, and two were verified against original page images because extraction disrupted text order. Source hashes, pages/sections and the image decisions are retained in the scoring inputs.',
        '', '## Parsing and execution','']
    parser=read(HERE/'parser_validation.json')
    for g in ['P0','P']:
        rows=[r for r in parser if r['group']==g]
        lines.append(f"- {g}: readable text events for {sum(r['readable_text'] for r in rows)}/81 files.")
    source_groups=all_records
    legacy=next(r['file'] for r in read(HERE/'inputs/corpus.json') if r['file'].endswith('.doc'))
    standards=all_standards
    direct=[r for r in standards if legacy in r['known_supporting_sources']]
    lines+=['', 'The legacy document is a verified source only for '+', '.join(r['id'] for r in direct)+'. Its direct effect therefore belongs to the combined-source results; the primary 98-question hit rate alone cannot measure this repair.']
    for q in direct:
        needed=set(q['required_sources'])
        details=[]
        for g in ['P0','P']:
            returned={r['file'] for r in source_groups[g][q['id']]['references']}
            details.append(f"{g}: {len(returned & needed)}/{len(needed)} required sources within ten; legacy source {'present' if legacy in returned else 'absent'}")
        lines+=['',q['id']+' — '+'; '.join(details)+'.']
    lines+=['',
        'The repaired legacy text matches the independently audited 85,278-character text after line-ending normalization. The adapter reads the original Word97 piece table, retains field codes and flattens table cells. It is limited to the single frozen legacy file. A readable text event is not proof of correct layout or complete extraction for every document.',
        '']
    for g in ['R2','R3','S','D']:
        r=groups[g]
        lines.append(f"- {g}: statuses {json.dumps(r['statuses'],sort_keys=True)}; median completed-stage time {r['median_query_s']:.2f}s; retrieval requests {r['calls']}, request errors {r['call_errors']}, reported tokens {r['total_tokens']:,}. Failed query attempts: {r['technical_attempts']}, taking {r['technical_attempt_seconds']:.2f}s excluding endpoint checks and downtime.")
    manifest=read(HERE/'review_inputs/manifest.json')
    adjfile=HERE/'support_reviews/adjudications.jsonl'
    adjudications=[json.loads(l) for l in adjfile.read_text(encoding='utf-8').splitlines()] if adjfile.exists() else []
    lines+=['',
        'All successful requests have matching outbound and returned runtime identifiers. Only technical failures may be retried, with every attempt retained. Empty retrieval is a valid completed miss. Source checks run after retrieval. S/D costs are stage-only, while R1 timing included concurrent source checks; do not interpret these medians as an isolated speed comparison.',
        '', 'Execution spans October 23 and October 25, 2026 (UTC), with network interruptions and resumed process segments. Completed results were retained. Reported request usage excludes unavailable usage from interrupted requests; wall-clock downtime is not retrieval latency. See the execution record and supervisor events for recovery details.',
        '',f"The source-check pool contains {manifest['pooled_unlisted_associations']} distinct unlisted question/source associations: {manifest['reused']} compatible previous decisions and {manifest['new_or_upgraded_jobs']} new or upgraded jobs. New source checks used {s['source_check_usage']['calls']} requests and {s['source_check_usage']['total_tokens']:,} reported tokens, separate from retrieval. The previously completed baseline source checks are not charged again in this total.",
        '',f"{len(adjudications)} source associations received additional direct text or rendered-page review. The decisions and exact evidence are retained in [adjudications](../support_reviews/adjudications.jsonl); original check records remain intact. Usage includes the first source-check pool and the refresh after parser correction, including earlier checks that are no longer needed by the final pool. See the [pool refresh](../parser_correction_review_refresh.json).",
        '', '## Limits','',
        'All questions were already exposed in earlier work. This is descriptive regression testing, not an unseen holdout evaluation. No settings were tuned against these follow-up scores. Snapshot reranking includes cached text for eight documents, but does not test systematic full-text reranking of every candidate. Directory budget, ranking and parsing are isolated comparisons; their combined effect was not tested. No product acceptance threshold or production-scale claim is inferred.',
        '',f"Artifact validation: {sum(c['passed'] for c in checks['checks'])}/{len(checks['checks'])} checks passed.",
        '', '## Artifacts','',
        '- [All question scores](questions.csv) and [ordered references](references.csv).',
        '- [Repeated-run agreement](stability.csv), [paired changes](transitions.csv), and [document averages](by_document.csv).',
        '- [Similar-question pairs](pairs.csv), [combined sources](cross_document.csv), and [negative cases](unanswerable.csv).',
        '- [Directory and parser diagnostics](stage_diagnostics.json), [environment verification](environment_validation.json), and [execution record](../EXECUTION.md).',
        '- [Source anchors](../scoring_inputs/standards_with_anchors.json), [page decisions](../scoring_inputs/anchor_adjudications.json), and [validation](validation.json).',
        '- [Plan](../PLAN.md), [execution guide](../README.md), and [machine-readable summary](summary.json).','']
    (HERE/'reports/REPORT.md').write_text('\n'.join(lines),encoding='utf-8')


if __name__=='__main__': main()
