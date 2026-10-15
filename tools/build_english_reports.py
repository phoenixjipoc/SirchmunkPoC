"""Publish English views of the recorded campaign; no search or model calls."""
import csv
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CAMPAIGN = ROOT / 'poc/results/20261014_ABC_verified120'
OUT = ROOT / 'reports/verified120'
HINTS = {
    '\u8fd0\u884c\u5f02\u5e38': 'Runtime error',
    '\u590d\u7528\u540e\u56de\u7b54\u6709\u8bef\u6216\u4e0d\u5b8c\u6574\uff1b\u9700\u6838\u5bf9\u662f\u5426\u590d\u7528\u4e86\u4e0d\u9002\u7528\u7684\u7c07': 'Incorrect or incomplete answer after reuse; check cluster applicability',
    '\u65e0\u7b54\u6848\u9898\u7ed9\u51fa\u5177\u4f53\u56de\u7b54': 'Concrete answer to an unanswerable question',
    '\u5019\u9009\u6587\u4ef6\u672a\u547d\u4e2d\u5df2\u77e5\u53c2\u8003\u6765\u6e90': 'Candidate files did not include a known reference source',
    '\u6709\u5019\u9009\u4f46\u91c7\u6837\u6587\u4ef6\u672a\u547d\u4e2d\u5df2\u77e5\u53c2\u8003\u6765\u6e90': 'Candidates existed, but sampled files missed known reference sources',
    '\u7cfb\u7edf\u62d2\u7b54\uff1b\u7ed3\u5408\u95e8\u63a7\u524d\u7b54\u6848\u4e0e\u8bc1\u636e\u590d\u6838': 'System returned no result; inspect the pre-gate answer and evidence',
    '\u672a\u8bb0\u5f55\u6765\u81ea\u53c2\u8003\u6765\u6e90\u7684\u80af\u5b9a\u8bc1\u636e': 'No positive evidence from a reference source was recorded',
    '\u8bc1\u636e\u5185\u5bb9\u6216\u7b54\u6848\u6c47\u603b\u4e0d\u5b8c\u6574/\u9519\u8bef\uff1b\u6587\u4ef6\u547d\u4e2d\u4e0d\u80fd\u786e\u5b9a\u539f\u56e0': 'Evidence or answer synthesis incomplete/incorrect; file hits alone do not establish the cause',
}
TRANSLATIONS = {r['source_sha256']: r for r in json.loads((ROOT/'tools/english_translations.json').read_text(encoding='utf-8'))}


def read_csv(path):
    with path.open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


def translated_value(field, value):
    if field == 'diagnostic_hint':
        return HINTS.get(value, value)
    fingerprint = hashlib.sha256(value.encode('utf-8')).hexdigest()
    return TRANSLATIONS.get(fingerprint, {}).get('english', value)


def publish_csv(source, destination):
    rows = read_csv(source)
    if not rows:
        return
    for row in rows:
        translated = []
        for key, value in list(row.items()):
            new = translated_value(key, value)
            if new != value:
                translated.append(key)
            row[key] = new
        row['publication_translation_note'] = (
            'English presentation translation: '+', '.join(translated)+'. Original evidence is unchanged.'
            if translated else '')
    with destination.open('w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def table(headers, rows):
    return '\n'.join(['| '+' | '.join(headers)+' |', '| '+' | '.join(['---']*len(headers))+' |',
                     *['| '+' | '.join(str(v).replace('|','/') for v in row)+' |' for row in rows]])


FINDINGS = '''## Findings

- B used 44.28% fewer search tokens than A, with six fewer correct answers and no median speed improvement. Candidate coverage was similar; sampled-source coverage fell. File coverage alone does not prove the required fact was read.
- All nine C reuse hits were wrong. A answered the same IDs with four correct, four no-results, and one wrong. C gained five correct answers on the other 111 questions, producing a net gain of one. This does not establish a reuse benefit.
- Reuse hits averaged 1.72 seconds and 201 tokens, versus A's 39.31 seconds and 100,261 tokens on those IDs. Across all questions, C used 16.64% fewer tokens but had a 2.70-second higher median.
- Seven hits involved predefined pairs; SVC-20 and CONS-07 were outside them. Wrong-version matches reached 0.994 and 0.993 similarity. The reuse function checks similarity and usable content, without a new factual-applicability check inside that function.
- No broad question was fully correct (13 per run). All nine negative questions received accepted refusals; this does not imply that other answers were factually correct.

## Limits and incidents

- A's Unicode export was repaired without rerunning search or grading. Original/fixed code hashes and the regression result are recorded.
- C/SVC-03 recovered through retry; 137.83 seconds and 148,219 tokens remain included. A/B/C had 5/2/3 serialization recoveries and no unrecovered runtime errors.
- Each stage had two direct-document routes with a separate five-file default. CONS-16 missed the ten named files. The legacy DOC's parsing corruption was retained across runs.
- SVC-15 has ambiguous audit scope. Excluding it gives 62.18% / 57.14% / 63.03%; main scores retain all questions.
- Scoring and secondary review were automated using the same configured service as search. All 190 required reviews were resolved. Initial and final decisions remain separate; no human sign-off was performed.
- Timing excludes preparation, scoring, review, and export. Usage includes successful sampling calls; failed calls may have unreported usage. The 128,000-token setting is not a strict cap.
- These are one-pass results on selected questions. C uses only earlier C clusters; identical-question replay and production-scale performance were not tested.

The campaign retains 360 responses and 238 clusters: A=82, B=76, C=80. Structural checks confirm unchanged source files, inputs, and recorded answers; they do not establish every semantic grade. See the methodology for full definitions.
'''


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    names = ['summary.csv','all_results.csv','question_comparison.csv','paired_results.csv',
             'review_queue.csv','failure_cases.csv','execution_routes.csv','transition_summary.csv',
             'sensitivity.csv','reuse_cases.csv','reuse_matched_comparison.csv']
    for name in names:
        publish_csv(CAMPAIGN/name, OUT/name)
    for stage in 'ABC':
        publish_csv(CAMPAIGN/stage/'clusters.csv', OUT/(stage+'_clusters.csv'))
    rows = read_csv(CAMPAIGN/'summary.csv')
    totals = [r for r in rows if r['group']=='ALL']
    overall = table(['Run','Correct / 120','Accuracy','Partial','Wrong','No answer','Error','P50 s','P95 s','Search tokens','Reuse hits'],
        [[r['stage'],int(r['correct'])+int(r['correct_refusal']),r['overall_correct_pct']+'%',r['partial'],r['wrong'],r['no_answer'],r['error'],r['p50_s'],r['p95_s'],r['total_tokens'],r['cluster_reuse_hits']] for r in totals])
    report = ['# Sirchmunk: 120-question A/B/C test report','',
        'Evaluation completed October 14, 2026. All 360 searches and all 190 required reviews are complete. This English edition preserves the original numerical results.','',
        '## Fixed conditions','',
        '81 documents; 120 verified questions in the same order; DEEP; Sirchmunk 0.0.7. A=k10/reuse off, B=k5/reuse off, C=k10/reuse on (threshold 0.85). Each run starts with an empty, separate knowledge store; only parsed-text cache is shared. C reuses only earlier clusters from C. Fifteen pairs have similar wording but different answers.','',
        'The [methodology](../../docs/METHODOLOGY.md) explains parsing, SDK execution, judging, and interpretation. The [execution log](../../poc/results/20261014_ABC_verified120/test_process.md) records actual commands and events.','',
        '## Overall results','',overall,'',
        'Correctness includes correct refusals; partial answers are not fully correct. There are 111 answerable and nine negative questions. No records are removed from the denominator.','',FINDINGS,
        '## Results by question type','']
    groups={ (r['stage'],r['group']):r for r in rows }
    typed=[]
    for typ in ['detail','pair_a','pair_b','medium','broad','unanswerable']:
        values=[typ,groups['A',typ]['n']]
        for s in 'ABC':
            r=groups[s,typ]; values.append(f"{int(r['correct'])+int(r['correct_refusal'])} / {r['overall_correct_pct']}%")
        typed.append(values)
    report.append(table(['Type','N','A correct / accuracy','B correct / accuracy','C correct / accuracy'],typed))
    cases=read_csv(CAMPAIGN/'reuse_cases.csv')
    report += ['', '## All actual reuse hits','',table(['Current ID','Source ID','Logged similarity','Final label','Seconds','Tokens'],
        [[r[k] for k in ['id','source_question_id','logged_similarity','final_label','latency_s','total_tokens']] for r in cases]),'',
        'Full questions, expected answers, reused answers and review reasons: [reuse_cases.csv](reuse_cases.csv).','']
    report += ['## Review and observability','', table(['Run','Primary accuracy','Label overrides','Coordinator reviews','Secondary reviews','Mechanical checks','Serialization errors','Incomplete citation traces'],
        [[r[k] for k in ['stage','initial_correct_pct','review_overrides','independently_reviewed','secondary_model_reviewed','mechanically_checked','serialization_errors','citation_trace_incomplete_count']] for r in totals]),'',
        'Review-method counts describe the final decision method per record and include proactive reviews outside the required queue. They are not three independent reviewers per question.','']
    report += ['## Paired and matched comparisons','']
    pairs=read_csv(CAMPAIGN/'paired_results.csv')
    report.append(table(['Run','Both questions correct / 15 pairs','Pair-B reused pair-A cluster'],
        [[s,sum(r['both_correct']=='True' for r in pairs if r['stage']==s),sum(r['b_reused_a_cluster']=='True' for r in pairs if r['stage']==s)] for s in 'ABC']))
    transitions=read_csv(CAMPAIGN/'transition_summary.csv')
    report += ['',table(['Comparison','Both correct','Gains','Regressions','Neither fully correct'],
        [[r['alternative']+' vs A',r['both_correct'],r['gains'],r['regressions'],r['neither_correct']] for r in transitions]),'']
    matched=read_csv(CAMPAIGN/'reuse_matched_comparison.csv')
    report.append(table(['Run','C-defined question cohort','N','Accuracy','Mean seconds','Mean tokens'],
        [[r[k] for k in ['stage','group','n','overall_correct_pct','mean_s','mean_tokens']] for r in matched]))
    report += ['','Groups are defined after observing C reuse behavior. This is a matched-ID descriptive comparison, not a randomized causal estimate.','',
        '## Source coverage','',table(['Run','Candidates','Sampled','Positive evidence','Cited','Cited observations'],
        [[r[k] for k in ['stage','gold_source_coverage_candidates','gold_source_coverage_sampled','gold_source_coverage_found_evidence','gold_source_coverage_cited','cited_coverage_observations']] for r in totals]),'',
        'Values are fractions, not percentages. Detailed execution-route and ambiguity sensitivity tables are included as CSV.','',
        '## English presentation files','',
        *['- ['+name+']('+name+')' for name in names],
        '- [A clusters](A_clusters.csv), [B clusters](B_clusters.csv), [C clusters](C_clusters.csv).','',
        'C / INV-04 and its cluster summary have explicit English translations. Each changed presentation row records the translation. Original responses, logs, and grade records are unchanged; no answer was regraded after translation.']
    (OUT/'report.md').write_text('\n'.join(report)+'\n',encoding='utf-8')
    (CAMPAIGN/'test_report.md').write_text('# A/B/C evaluation: English report\n\n'+overall+'\n\n'+
        'Read the [complete English report](../../../reports/verified120/report.md) for methodology, findings, all reuse hits, review accounting, and limitations.\n\n'+
        'Raw records remain here. See [final findings](final_findings.md) for interpretation and limits.\n',encoding='utf-8')
    (CAMPAIGN/'final_findings.md').write_text('# Final findings: English edition\n\n'+FINDINGS,encoding='utf-8')
    events=[json.loads(s) for s in (CAMPAIGN/'events.jsonl').read_text(encoding='utf-8').split('\n') if s.strip()]
    meta=json.loads((CAMPAIGN/'campaign.json').read_text(encoding='utf-8'))
    process=['# A/B/C execution record','',
        '81 raw files; 120 verified questions per stage; DEEP mode. A=k10/reuse off, B=k5/off, C=k10/on at similarity 0.85. Each stage starts with an empty cluster store; parsed-text cache is shared.','',
        'Search receives only IDs/questions. References and acceptance criteria are used later for automated scoring and separate review.','',
        '## Stage timing','',
        table(['Stage','Started','Completed','Questions','Clusters'],
              [[stage,meta['stages'][stage]['started'],meta['stages'][stage]['finished'],120,
                meta['stages'][stage]['clusters_exported']] for stage in 'ABC']),'',
        'Times are recorded with the +08:00 offset. Stage completion includes export; reviews and final adjudication follow.','',
        '## Recorded incidents','',
        '- The legacy DOC produced partially garbled text; it remained unchanged across all stages.',
        '- A completed search and grading before a Unicode JSONL export failure. Only export parsing was repaired; search was not rerun.',
        '- An early repair event prematurely claimed a test pass. The later `export_regression_test_passed` event records the actual result.',
        '- C/SVC-03 recovered through an automatic connection retry. Its timing and usage remain included.',
        '- CONS-16 took a direct-document route with a separate five-file default and missed the ten named RFPs.',
        '- Final review resolved all required disagreements; original labels were preserved.','',
        '## Completion and source records','',
        '360 responses, 190 required reviews resolved, and 238 clusters exported. Final correct counts: A=74, B=68, C=75.','',
        '[events.jsonl](events.jsonl) retains all '+str(len(events))+' events, commands, timestamps, and incident details. One parser-followup event has no recorded timestamp. [validation.json](validation.json) contains the original integrity checks.','',
        'Recorded commands refer to the original workspace. Use the [reproduction guide](../../../docs/REPRODUCING.md) for a new checkout.']
    (CAMPAIGN/'test_process.md').write_text('\n'.join(process)+'\n',encoding='utf-8')
    print(json.dumps({'presentation_csvs':len(names)+3,'search_records':360,'model_calls':0,'output':'reports/verified120'}))


if __name__ == '__main__':
    main()
