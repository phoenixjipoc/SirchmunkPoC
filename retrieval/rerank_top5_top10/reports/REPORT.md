# Top-five and top-ten reranking results

One pass per arm used all 120 questions and 81 original documents. Both new arms reused the same R1 retrieval lists. RR5 reordered positions 1-5 and preserved positions 6-10; RR10 reordered positions 1-10. No new discovery, final answers or knowledge clusters were produced.

## Document support

The primary denominator is 98 single-document questions. A qualifying document contains every mandatory fact for the correct organization, edition and conditions.

- Baseline: Hit@1 **52.04% (51/98)**; Hit@5 75.51% (74/98); Hit@10 81.63% (80/98). MRR@10 0.6284.
- RR5: Hit@1 **75.51% (74/98)**; Hit@5 75.51% (74/98); Hit@10 81.63% (80/98). MRR@10 0.7641.
- RR10: Hit@1 **80.61% (79/98)**; Hit@5 81.63% (80/98); Hit@10 81.63% (80/98). MRR@10 0.8095.

## Paired changes

- Baseline to RR10: 28 first-position gains, 0 losses; net change +28.57 percentage points.
- Baseline to RR5: 23 first-position gains, 0 losses; net change +23.47 percentage points.
- RR5 to RR10: 5 first-position gains, 0 losses; net change +5.10 percentage points.

Hit@10 is unchanged for every question because candidate membership is fixed. RR5 Hit@5 is also unchanged. Reranking cannot recover a source outside its candidate pool.

## Question types and similar pairs

- Baseline: first-position hits by type — detail: 28/50; medium: 9/18; pair_a: 8/15; pair_b: 6/15. Both questions hit first in 3/15 similar-question pairs; an opposite question's exclusive source ranks incorrectly first on 2/30 paired queries.
- RR5: first-position hits by type — detail: 41/50; medium: 12/18; pair_a: 11/15; pair_b: 10/15. Both questions hit first in 8/15 similar-question pairs; an opposite question's exclusive source ranks incorrectly first on 0/30 paired queries.
- RR10: first-position hits by type — detail: 43/50; medium: 15/18; pair_a: 11/15; pair_b: 10/15. Both questions hit first in 8/15 similar-question pairs; an opposite question's exclusive source ranks incorrectly first on 0/30 paired queries.

## Other 22 questions

- Baseline: complete required-source sets at five 1/12 and at ten 2/12; mean source coverage at five 32.50% and at ten 40.83%. The thematic question retrieves 3/6 listed example sources at five and 3/6 at ten.
- RR5: complete required-source sets at five 1/12 and at ten 2/12; mean source coverage at five 32.50% and at ten 40.83%. The thematic question retrieves 3/6 listed example sources at five and 3/6 at ten.
- RR10: complete required-source sets at five 2/12 and at ten 2/12; mean source coverage at five 40.83% and at ten 40.83%. The thematic question retrieves 3/6 listed example sources at five and 3/6 at ten.

The nine negative cases retain document suggestions only. No refusal accuracy or false-answer rate is inferred.

## Execution and cost

- RR5: 120 completed tasks; statuses {'skipped_single': 24, 'ok': 92, 'fallback_original': 1, 'skipped_empty': 3}. Ranking requests 95, request errors 3, reported tokens 104,236 (91,869 input, 12,367 output). Request median 2.832s, p95 5.240s.
- RR10: 120 completed tasks; statuses {'skipped_single': 24, 'ok': 93, 'skipped_empty': 3}. Ranking requests 93, request errors 0, reported tokens 159,443 (144,453 input, 14,990 output). Request median 3.195s, p95 4.660s.

Preflight: 4 requests and 45 tokens. Separate source checks: 14 new requests and 326,889 tokens, covering 14 new or upgraded associations; 459 compatible associations reused. Existing verified positive sources retain their original audit.

Ranking time is stage-only and excludes source checking, container startup and input preparation. P95 uses the nearest-rank percentile. Historical full-search timings are not a matched comparison. The first smoke question had one candidate and used the skip path; subsequent nontrivial tasks exercised permutation validation. Completed tasks were never repeated for a better score.

A connection interruption exhausted three attempts for RR5 XD-01. Its original order remains the reported result, with a technical-fallback flag; it remains in the 98-question denominator. The failed recovery check stopped further tasks. A later successful preflight resumed unfinished work with unchanged settings. All 97 previously completed result hashes were retained.

## Examples

- Baseline->RR5, INV-05 (gain): `TRS_Illinois__FY23-RFP-Investment-Consultant-final_7.pdf` at first changes to `TRS_Illinois__FY25-RFP-Private-Equity-Investment-Consultant.pdf`. First supported rank: 2 to 1.
- Baseline->RR5, INV-07 (gain): `TRS_Illinois__FY23-RFP-Investment-Consultant-final_7.pdf` at first changes to `Creve_Coeur_MO__Questions-and-Answers-from-RFP-for-Pension-Consulting-Services.pdf`. First supported rank: 2 to 1.
- Baseline->RR10, INV-05 (gain): `TRS_Illinois__FY23-RFP-Investment-Consultant-final_7.pdf` at first changes to `TRS_Illinois__FY25-RFP-Private-Equity-Investment-Consultant.pdf`. First supported rank: 2 to 1.
- Baseline->RR10, INV-07 (gain): `TRS_Illinois__FY23-RFP-Investment-Consultant-final_7.pdf` at first changes to `Creve_Coeur_MO__Questions-and-Answers-from-RFP-for-Pension-Consulting-Services.pdf`. First supported rank: 2 to 1.
- RR5->RR10, SVC-19 (gain): `Delaware__TRE21101-RECDKEEPR-rfp.pdf` at first changes to `Temple_City_CA__Recordkeeping-RFP.pdf`. First supported rank: 6 to 1.
- RR5->RR10, XD-14 (gain): `ILPA__ILPA-DDQ-2.0.pdf` at first changes to `NJEDA__NJEDA-LIFE-SCIENCE-SEED-FUND-NOTICE-OF-INVESTMENT-OPPORTUNITY-ISSUED-2023-02-09-.pdf`. First supported rank: 7 to 1.

## Interpretation and limits

These results measure reranking from filenames, titles, keywords and previews of at most 800 characters. Eight cached full-content fields were excluded. Three corpus documents have empty saved previews and therefore rely on the remaining metadata when present among candidates. Source scoring used complete original-derived text and the existing evidence audit.

Both arms received identical fields for shared documents, with a fixed hash-based presentation order and hidden original ranks. Runtime identity was checked in outgoing requests and responses. Source checks ran afterward and did not feed back into ranking.

This is an exposed benchmark with one pass per arm. It does not establish unseen performance, repeated-run stability or a product acceptance threshold. Preview truncation can hide relevant facts. More candidates can also introduce competing documents, so RR10 need not outperform RR5 on every question.

## Files

- [Plan](../PLAN.md), [settings](../settings.json) and [frozen inputs](../freeze.json).
- [All 360 scores](questions.csv), [ordered references](references.csv) and [paired changes](transitions.csv).
- [Similar pairs](pairs.csv), [combined sources](cross_document.csv), [negative cases](unanswerable.csv) and [document averages](by_document.csv).
- [Summary](summary.json), [validation](validation.json) and [source-check jobs](../review_inputs/manifest.json).
