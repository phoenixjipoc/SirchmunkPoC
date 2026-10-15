# Final findings: English edition

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
