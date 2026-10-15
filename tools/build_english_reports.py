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


FINDINGS = '''## Interpretation

B used 44.28% fewer search tokens than A, but answered six fewer questions fully correctly. Its median latency was 39.68 seconds versus A's 38.75 seconds; no median latency improvement was observed. Candidate-source coverage was similar, while sampled-source coverage was lower. Coverage is a diagnostic clue, not proof that the required facts were read.

C's overall score was one question higher than A's. However, all nine actual reuse hits were wrong. The same nine IDs in A produced four correct answers, four no-results, and one wrong answer. The other 111 IDs gained a net five correct answers in C, offsetting the four lost correct answers in the reuse group. One-pass differences on fresh searches remain subject to model and sampling variation; the aggregate score does not establish a benefit from reuse.

Reuse hits averaged 1.72 seconds and 201 tokens, versus 39.31 seconds and 100,261 tokens for A on the same nine question IDs. This acceleration came with nine unsuitable answers. Across all 120 questions, C used 16.64% fewer search tokens than A, but its median latency was 2.70 seconds higher. These stress-test questions do not estimate the distribution of normal business traffic.

Seven reuse hits came from the second question in a predefined pair. Two came from other questions: SVC-20 reused SVC-15's contract-term cluster to answer a services-scope question, and CONS-07 reused CONS-06's TMRS identification for an OCERS requirement. Wrong-version ILPA matches had similarities of 0.994 and 0.993. The inspected reuse function returns existing cluster content after similarity/content checks without a new factual-applicability check inside that function. Raising the threshold alone would leave some observed failures; matching the document alone would not resolve the KCERA different-fact example.

Cross-document synthesis remains a major limitation: all three runs scored zero fully correct out of 13 broad questions, with six, six, and five partial answers respectively. This does not mean the answers contained no relevant information. All nine negative questions were correctly refused in every run. Detail-question correctness was 40/50, 34/50, and 40/50.

Use A (k10, reuse off) as the next comparison baseline. Before enabling approximate reuse, validate the institution, version, mandate, and requested fact against the current question, falling back to fresh retrieval when unsupported. Improve relevant-file enumeration and cross-document coverage, including the direct-document intent route, then rerun the complete benchmark. No search-library changes or extra evaluation runs were made during publication.

## Incidents, audit scope, and limitations

- A's cluster export initially failed on U+2029 inside evidence text. Only JSONL export handling was repaired; completed search and judge records were reused. The original/fixed hashes and the passing export regression test are preserved.
- C / SVC-03 recovered through an automatic retry after a connection error. The observed 137.83 seconds and 148,219 tokens were retained; the outlier was not removed.
- A/B/C had 5/2/3 return-object serialization errors, respectively. The harness recovered and graded the answers. There were zero unrecovered runtime errors, but HTTP end-to-end availability was not evaluated.
- Every stage had two direct-document intent routes. The default collector takes at most five files independently of top_k; CONS-16 consequently did not read the ten named RFPs. Installed source excerpts and raw records are included.
- The legacy INREV DOC contains substantial extraction corruption. Its raw bytes and runtime handling were kept identical across A/B/C. Independent audit extraction was not substituted into retrieval.
- SVC-15 ambiguously says audit services without specifying financial versus actuarial audit. Main scores retain the frozen reference. Excluding it gives A 62.18%, B 57.14%, C 63.03%; this is a sensitivity view, not replacement scoring.
- The primary judge and separate secondary-review requests used the same configured model as search. The coordinating AI additionally checked cases and resolved disagreements. This is not a human-certified benchmark, and semantic completeness judgments still require interpretation.
- All initially non-correct results and a reproducible roughly 20% sample of initially correct/refusal results were selected for review: 190 records, all resolved. Other cases were also reviewed. Initial and secondary labels remain preserved separately from final decisions.
- Source coverage is a per-question fraction of known reference files reached. A file hit does not establish factual support. Missing citation metadata from serialization failures or directory-only citations is excluded from the cited-coverage mean and its missing count is reported.
- Latency excludes prewarm, judging, review, and export. Search token totals use successful model-wrapper response usage, including child sampling calls; unreported internal retry usage may be missing. Monetary costs were not estimated.
- The 128,000-token runtime budget parameter is not a strict cap after parallel calls/retries. Scores and usage in this repository refer to the verified 120-question campaign.
- C asks 120 distinct questions once. It does not use A/B clusters and does not test exact-question replay. Nine cache failures in this stress test do not quantify all possible reuse scenarios.
- The structural validator confirms 360 records, unchanged hashes for 81 originals, identical questions/image/model, isolated knowledge paths, search input without gold answers, and preserved answers/usage. It does not prove every semantic grade is correct.

Knowledge clusters exported: A 82, B 76, C 80 (238 total). Original logs, raw JSON, frozen inputs and code, traces, and stage-specific cluster CSV/JSONL files remain in the campaign directory.
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
        '81 original documents; the same 120 verified questions and order; DEEP; Sirchmunk 0.0.7; gpt-5.4. A=k10/reuse off, B=k5/reuse off, C=k10/reuse on (threshold 0.85). Each run starts with an empty, separate knowledge store; only parsed-text cache is shared. C reuses only earlier clusters from C. Fifteen pairs have similar wording but different answers.','',
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
    report += ['## Review and observability','', table(['Run','Primary accuracy','Label overrides','Coordinator reviews','Secondary model reviews','Mechanical checks','Serialization errors','Incomplete citation traces'],
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
        'One C / INV-04 model answer and its cluster summary were translated from Chinese. Each changed presentation row records the translation. Original responses, logs, and grade records are unchanged; no answer was regraded after translation.']
    (OUT/'report.md').write_text('\n'.join(report)+'\n',encoding='utf-8')
    (CAMPAIGN/'test_report.md').write_text('# A/B/C evaluation: English report\n\n'+overall+'\n\n'+
        'Read the [complete English report](../../../reports/verified120/report.md) for methodology, findings, all reuse hits, review accounting, and limitations.\n\n'+
        'Original raw records remain in this directory. English presentation tables are under `reports/verified120/`.\n'+FINDINGS,encoding='utf-8')
    (CAMPAIGN/'final_findings.md').write_text('# Final findings: English edition\n\n'+FINDINGS,encoding='utf-8')
    events=[json.loads(s) for s in (CAMPAIGN/'events.jsonl').read_text(encoding='utf-8').split('\n') if s.strip()]
    process=['# A -> B -> C execution process','',
        'All stages use 120 verified questions, 81 original files, DEEP mode and serial questions. A=k10/reuse off; B=k5/reuse off; C=k10/reuse on at 0.85. Each stage starts with an empty knowledge store; the parsed-text cache is shared.','',
        'Search input contains only IDs/questions. Frozen references and acceptance criteria are used later for grading. Primary and secondary model judging share the search model configuration; coordinating review is separately recorded.','',
        'The legacy DOC parser issue was retained throughout all stages. A JSONL export failure was repaired without rerunning search. Connection retries and serialization recoveries remain in the metrics and logs.','',
        'Events below preserve the original order and timestamps. Historical command paths refer to the original workspace; use the reproduction guide for the new checkout. The first exporter-repair event prematurely reported a test pass; the later `export_regression_test_passed` event explicitly corrects that record.','',
        '## Execution events','']
    for e in events:
        details={k:v for k,v in e.items() if k not in ['time','event']}
        recorded_time=e.get('time','Timestamp not recorded in the original event')
        process += [f"- **{recorded_time}** `{e['event']}`",'','```json',json.dumps(details,ensure_ascii=False,indent=2),'```','']
    process += ['## Completion','', '360 search records, all 190 required review records resolved, and 238 clusters exported. See `validation.json` for original data-integrity checks. Publication/translation checks are recorded separately in the repository provenance directory.']
    (CAMPAIGN/'test_process.md').write_text('\n'.join(process)+'\n',encoding='utf-8')
    print(json.dumps({'presentation_csvs':len(names)+3,'search_records':360,'model_calls':0,'output':'reports/verified120'}))


if __name__ == '__main__':
    main()
