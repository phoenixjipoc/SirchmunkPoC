# Sirchmunk: 120-question A/B/C test report

Evaluation completed October 14, 2026. All 360 searches and all 190 required reviews are complete. This English edition preserves the original numerical results.

## Fixed conditions

81 original documents; the same 120 verified questions and order; DEEP; Sirchmunk 0.0.7; gpt-5.4. A=k10/reuse off, B=k5/reuse off, C=k10/reuse on (threshold 0.85). Each run starts with an empty, separate knowledge store; only parsed-text cache is shared. C reuses only earlier clusters from C. Fifteen pairs have similar wording but different answers.

The [methodology](../../docs/METHODOLOGY.md) explains parsing, SDK execution, judging, and interpretation. The [execution log](../../poc/results/20261014_ABC_verified120/test_process.md) records actual commands and events.

## Overall results

| Run | Correct / 120 | Accuracy | Partial | Wrong | No answer | Error | P50 s | P95 s | Search tokens | Reuse hits |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A | 74 | 61.67% | 8 | 12 | 26 | 0 | 38.75 | 47.93 | 11117348 | 0 |
| B | 68 | 56.67% | 9 | 11 | 32 | 0 | 39.68 | 51.84 | 6194941 | 0 |
| C | 75 | 62.5% | 7 | 17 | 21 | 0 | 41.45 | 58.55 | 9267393 | 9 |

Correctness includes correct refusals; partial answers are not fully correct. There are 111 answerable and nine negative questions. No records are removed from the denominator.

## Interpretation

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

## Results by question type

| Type | N | A correct / accuracy | B correct / accuracy | C correct / accuracy |
| --- | --- | --- | --- | --- |
| detail | 50 | 40 / 80.0% | 34 / 68.0% | 40 / 80.0% |
| pair_a | 15 | 9 / 60.0% | 9 / 60.0% | 12 / 80.0% |
| pair_b | 15 | 7 / 46.67% | 6 / 40.0% | 4 / 26.67% |
| medium | 18 | 9 / 50.0% | 10 / 55.56% | 10 / 55.56% |
| broad | 13 | 0 / 0.0% | 0 / 0.0% | 0 / 0.0% |
| unanswerable | 9 | 9 / 100.0% | 9 / 100.0% | 9 / 100.0% |

## All actual reuse hits

| Current ID | Source ID | Logged similarity | Final label | Seconds | Tokens |
| --- | --- | --- | --- | --- | --- |
| INV-12 | INV-11 | 0.882 | wrong | 1.55 | 204 |
| INV-14 | INV-13 | 0.928 | wrong | 1.92 | 203 |
| SVC-20 | SVC-15 | 0.862 | wrong | 1.48 | 196 |
| XD-10 | XD-09 | 0.994 | wrong | 1.5 | 200 |
| CONS-07 | CONS-06 | 0.889 | wrong | 1.75 | 209 |
| CONS-11 | CONS-10 | 0.854 | wrong | 1.7 | 188 |
| CONS-13 | CONS-12 | 0.866 | wrong | 1.72 | 197 |
| DDQ-07 | DDQ-06 | 0.993 | wrong | 2.05 | 203 |
| DDQ-09 | DDQ-08 | 0.989 | wrong | 1.8 | 208 |

Full questions, expected answers, reused answers and review reasons: [reuse_cases.csv](reuse_cases.csv).

## Review and observability

| Run | Primary accuracy | Label overrides | Coordinator reviews | Secondary model reviews | Mechanical checks | Serialization errors | Incomplete citation traces |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A | 61.67 | 2 | 56 | 13 | 11 | 5 | 7 |
| B | 55.0 | 7 | 23 | 16 | 33 | 2 | 4 |
| C | 61.67 | 2 | 38 | 16 | 21 | 3 | 5 |

Review-method counts describe the final decision method per record and include proactive reviews outside the required queue. They are not three independent reviewers per question.

## Paired and matched comparisons

| Run | Both questions correct / 15 pairs | Pair-B reused pair-A cluster |
| --- | --- | --- |
| A | 6 | 0 |
| B | 4 | 0 |
| C | 4 | 7 |

| Comparison | Both correct | Gains | Regressions | Neither fully correct |
| --- | --- | --- | --- | --- |
| B vs A | 62 | 6 | 12 | 40 |
| C vs A | 66 | 9 | 8 | 37 |

| Run | C-defined question cohort | N | Accuracy | Mean seconds | Mean tokens |
| --- | --- | --- | --- | --- | --- |
| A | C_reuse_hit | 9 | 44.44 | 39.31 | 100261 |
| C | C_reuse_hit | 9 | 0.0 | 1.72 | 200.89 |
| A | C_no_reuse_hit | 111 | 63.06 | 39.02 | 92027.02 |
| C | C_no_reuse_hit | 111 | 67.57 | 42.42 | 83473.74 |

Groups are defined after observing C reuse behavior. This is a matched-ID descriptive comparison, not a randomized causal estimate.

## Source coverage

| Run | Candidates | Sampled | Positive evidence | Cited | Cited observations |
| --- | --- | --- | --- | --- | --- |
| A | 0.8874 | 0.7597 | 0.7559 | 0.7247 | 107 |
| B | 0.9017 | 0.6571 | 0.6571 | 0.6277 | 107 |
| C | 0.8311 | 0.6946 | 0.6931 | 0.7131 | 108 |

Values are fractions, not percentages. Detailed execution-route and ambiguity sensitivity tables are included as CSV.

## English presentation files

- [summary.csv](summary.csv)
- [all_results.csv](all_results.csv)
- [question_comparison.csv](question_comparison.csv)
- [paired_results.csv](paired_results.csv)
- [review_queue.csv](review_queue.csv)
- [failure_cases.csv](failure_cases.csv)
- [execution_routes.csv](execution_routes.csv)
- [transition_summary.csv](transition_summary.csv)
- [sensitivity.csv](sensitivity.csv)
- [reuse_cases.csv](reuse_cases.csv)
- [reuse_matched_comparison.csv](reuse_matched_comparison.csv)
- [A clusters](A_clusters.csv), [B clusters](B_clusters.csv), [C clusters](C_clusters.csv).

One C / INV-04 model answer and its cluster summary were translated from Chinese. Each changed presentation row records the translation. Original responses, logs, and grade records are unchanged; no answer was regraded after translation.
