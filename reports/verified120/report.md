# Sirchmunk: 120-question A/B/C test report

Evaluation completed October 14, 2026. All 360 searches and all 190 required reviews are complete. This English edition preserves the original numerical results.

## Fixed conditions

81 documents; 120 verified questions in the same order; DEEP; Sirchmunk 0.0.7. A=k10/reuse off, B=k5/reuse off, C=k10/reuse on (threshold 0.85). Each run starts with an empty, separate knowledge store; only parsed-text cache is shared. C reuses only earlier clusters from C. Fifteen pairs have similar wording but different answers.

The [methodology](../../docs/METHODOLOGY.md) explains parsing, SDK execution, judging, and interpretation. The [execution log](../../poc/results/20261014_ABC_verified120/test_process.md) records actual commands and events.

## Overall results

| Run | Correct / 120 | Accuracy | Partial | Wrong | No answer | Error | P50 s | P95 s | Search tokens | Reuse hits |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A | 74 | 61.67% | 8 | 12 | 26 | 0 | 38.75 | 47.93 | 11117348 | 0 |
| B | 68 | 56.67% | 9 | 11 | 32 | 0 | 39.68 | 51.84 | 6194941 | 0 |
| C | 75 | 62.5% | 7 | 17 | 21 | 0 | 41.45 | 58.55 | 9267393 | 9 |

Correctness includes correct refusals; partial answers are not fully correct. There are 111 answerable and nine negative questions. No records are removed from the denominator.

## Findings

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

| Run | Primary accuracy | Label overrides | Coordinator reviews | Secondary reviews | Mechanical checks | Serialization errors | Incomplete citation traces |
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

C / INV-04 and its cluster summary have explicit English translations. Each changed presentation row records the translation. Original responses, logs, and grade records are unchanged; no answer was regraded after translation.
