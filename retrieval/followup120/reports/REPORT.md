# Retrieval follow-up results

The same 120 questions and 81 raw documents were retained. There are 98 single-document questions, twelve required-source combinations, one thematic question and nine negative cases. No final answers or knowledge clusters were produced.

## Repeated runs

- R1, Original baseline: Hit@1 52.04% (51/98); Hit@5 75.51% (74/98); Hit@10 81.63% (80/98). MRR@10 0.6284.
- R2, Repeat, seed 17012: Hit@1 52.04% (51/98); Hit@5 73.47% (72/98); Hit@10 78.57% (77/98). MRR@10 0.6132.
- R3, Repeat, seed 17013: Hit@1 45.92% (45/98); Hit@5 71.43% (70/98); Hit@10 77.55% (76/98). MRR@10 0.5767.

Mean Hit@1 was 50.00%, with a 45.92%–52.04% range. 32/98 questions hit in all three runs; 28/98 missed in all three; 38/98 changed between hit and miss. The first filename changed on 56/98 questions. These are repeated observations of 98 questions, not 294 independent questions.

## Controlled comparisons

- S, Fixed-candidate reranking: Hit@1 80.61% (79/98); Hit@5 81.63% (80/98); Hit@10 81.63% (80/98). MRR@10 0.8095. First-position changes against R1: gains 28, losses 0.
- D, All 81 directory candidates: Hit@1 55.10% (54/98); Hit@5 84.69% (83/98); Hit@10 91.84% (90/98). MRR@10 0.6855. First-position changes against R1: gains 4, losses 1.
- P, Fixed-order keyword replay with parser repair: Hit@1 51.02% (50/98); Hit@5 75.51% (74/98); Hit@10 79.59% (78/98). MRR@10 0.6188. First-position changes against P0: gains 0, losses 0.

S permutes the original first ten candidates using the question and frozen directory snapshot. The snapshot contains metadata/previews and cached full text for eight short documents; those cached fields are also supplied. The candidate set stays fixed; valid permutations cannot change Hit@10. D reuses the original keyword results and changes only the directory-stage candidate budget from twenty to 81. Its result remains keyword-first. These are stage-level comparisons, not new complete search runs.

P0: Hit@1 51.02% (50/98), Hit@10 79.59% (78/98). P and P0 replay identical frozen keyword terms and directory results on the original files. Both use fixed file-path order; P alone enables the corpus-specific legacy Word parser through the live asynchronous executor. This is a parsing diagnostic, not a proposed relevance-ranking method. Compare P with P0, not directly with R1.

The initial parser comparison patched an unused synchronous function. Those invalid comparison records are preserved separately. A real keyword-tool integration check passed before the corrected 120-question replay. See the [correction record](../PARSER_CORRECTION.md).

## Examples

- INV-12: reranking moves the IMRF investment-manager RFP ahead of the similarly named consulting RFP. [S result](../runs/S/queries/INV-12.json).
- CONS-07: S still puts the TMRS consulting RFP first; the qualifying OCERS document remains third. Snapshot reranking does not resolve this numeric-qualification query. [S result](../runs/S/queries/CONS-07.json).
- DDQ-08: the baseline returns no file; D returns the required ILPA FAQ first. [D result](../runs/D/queries/DDQ-08.json).
- SVC-07: D puts the SBCERS custody RFP ahead of the required TMRS custody RFP, moving the correct file from first to second. [D result](../runs/D/queries/SVC-07.json).

## Similar questions and combined sources

- R1: both questions hit first in 3/15 pairs; both hit within ten in 8/15. An opposite pair's exclusive source appeared incorrectly first on 2/30 paired queries. Required-source sets were complete within ten for 2/12 questions, with mean source coverage 40.83%.
- R2: both questions hit first in 4/15 pairs; both hit within ten in 9/15. An opposite pair's exclusive source appeared incorrectly first on 3/30 paired queries. Required-source sets were complete within ten for 2/12 questions, with mean source coverage 38.33%.
- R3: both questions hit first in 1/15 pairs; both hit within ten in 10/15. An opposite pair's exclusive source appeared incorrectly first on 6/30 paired queries. Required-source sets were complete within ten for 2/12 questions, with mean source coverage 39.65%.
- S: both questions hit first in 8/15 pairs; both hit within ten in 8/15. An opposite pair's exclusive source appeared incorrectly first on 0/30 paired queries. Required-source sets were complete within ten for 2/12 questions, with mean source coverage 40.83%.
- D: both questions hit first in 5/15 pairs; both hit within ten in 12/15. An opposite pair's exclusive source appeared incorrectly first on 2/30 paired queries. Required-source sets were complete within ten for 4/12 questions, with mean source coverage 58.89%.
- P0: both questions hit first in 1/15 pairs; both hit within ten in 8/15. An opposite pair's exclusive source appeared incorrectly first on 3/30 paired queries. Required-source sets were complete within ten for 2/12 questions, with mean source coverage 40.83%.
- P: both questions hit first in 1/15 pairs; both hit within ten in 8/15. An opposite pair's exclusive source appeared incorrectly first on 3/30 paired queries. Required-source sets were complete within ten for 2/12 questions, with mean source coverage 42.92%.

Thematic question DDQ-11, listed example sources within ten: R1 3/6; R2 4/6; R3 3/6; S 3/6; D 6/6; P0 3/6; P 3/6.

Negative queries returning one or more suggestions: R1 9/9; R2 9/9; R3 9/9; S 9/9; D 9/9; P0 9/9; P 9/9.

The thematic question has a non-exhaustive example-source set and is reported separately. Negative queries produce document suggestions without an answerability decision; neither refusal accuracy nor a false-answer rate is inferred.

## Source-path diagnostics

- K, Keyword-only diagnostic: Hit@1 50.00% (49/98), Hit@10 78.57% (77/98).
- T, Directory-only diagnostic: Hit@1 17.35% (17/98), Hit@10 17.35% (17/98).

K and T replay the original path outputs. They do not rerun discovery or measure independent search latency.

Native keyword scoring reorders matching lines within each file, then retains the file discovery order. The harness merges keyword files before directory files; it does not perform a global relevance ranking of documents. In the archived initial parser replay, both arms used the default parser and identical keywords, yet 73/120 file orders changed while candidate membership stayed unchanged. This demonstrates an ordering source of instability separate from keyword generation and directory sampling. See the [initial diagnostics](../parser_initial_invalid/stage_diagnostics.json).

D included and returned ranking records for all 81 filenames on every query. High-relevance files absent from the supplied candidates occurred on 0 queries. All 98 verified single-document sources occurred in the merged candidate lists; eight fell beyond the ten-file cutoff.

Keyword order changed on 71/120 queries between R1 and P0, and on 13/120 between P0 and P. Excluding the legacy file, P0/P order changed on 0/120 and membership changed on 0/120. The legacy file appeared in keyword results on 0 control queries and 13 repaired queries. The fixed-order comparison isolates parser effects from native file-order variation.

## Question types and failures

- R1 first-position hits by type: detail: 28/50; medium: 9/18; pair_a: 8/15; pair_b: 6/15. Equal-weight document average: 52.72%.
- R2 first-position hits by type: detail: 26/50; medium: 12/18; pair_a: 7/15; pair_b: 6/15. Equal-weight document average: 52.72%.
- R3 first-position hits by type: detail: 23/50; medium: 10/18; pair_a: 5/15; pair_b: 7/15. Equal-weight document average: 46.78%.
- S first-position hits by type: detail: 43/50; medium: 15/18; pair_a: 11/15; pair_b: 10/15. Equal-weight document average: 80.23%.
- D first-position hits by type: detail: 28/50; medium: 10/18; pair_a: 9/15; pair_b: 7/15. Equal-weight document average: 55.73%.
- P0 first-position hits by type: detail: 26/50; medium: 11/18; pair_a: 7/15; pair_b: 6/15. Equal-weight document average: 50.89%.
- P first-position hits by type: detail: 26/50; medium: 11/18; pair_a: 7/15; pair_b: 6/15. Equal-weight document average: 50.89%.

R1 outcome categories: top1_hit: 51; support_rank_2_5: 23; absent_from_candidates: 11; support_rank_6_10: 6; beyond_cutoff: 4; empty_retrieval: 3.

S outcome categories: top1_hit: 79; absent_from_candidates: 11; outside_fixed_candidate_pool: 4; support_rank_2_5: 1; empty_retrieval: 3.

D outcome categories: top1_hit: 54; support_rank_2_5: 29; beyond_cutoff: 8; support_rank_6_10: 7.

P outcome categories: top1_hit: 50; support_rank_2_5: 24; absent_from_candidates: 11; beyond_cutoff: 6; support_rank_6_10: 4; empty_retrieval: 3.

Candidate absence and cutoff categories use the verified source list. Files outside the returned ten were not exhaustively assessed. A missed candidate alone does not establish a parsing or version-selection failure.

## Measurement and source checks

Document support requires all mandatory facts for the correct issuer, version and conditions. Hit@k means at least one qualifying document appears in the first k files. MRR@10 averages the reciprocal position of the first qualifying document, assigning zero when none occurs within ten. Equal-weight document averages are reported alongside question-level scores; the 98 single-document questions cover 73 documents.

Verified positives retain the completed source audit. Unlisted returned sources reuse compatible source checks or receive fresh full-text checks. Newly first-ranked unlisted sources receive two separate checks. Unresolved support remains explicit and produces score bounds. The same configured service is used for the separate checks; agreement is not independent proof.

All 360 preserved evidence anchors were checked: 358 matched normalized source text, and two were verified against original page images because extraction disrupted text order. Source hashes, pages/sections and the image decisions are retained in the scoring inputs.

## Parsing and execution

- P0: readable text events for 80/81 files.
- P: readable text events for 81/81 files.

The legacy document is a verified source only for XD-16. Its direct effect therefore belongs to the combined-source results; the primary 98-question hit rate alone cannot measure this repair.

XD-16 — P0: 0/4 required sources within ten; legacy source absent; P: 1/4 required sources within ten; legacy source present.

The repaired legacy text matches the independently audited 85,278-character text after line-ending normalization. The adapter reads the original Word97 piece table, retains field codes and flattens table cells. It is limited to the single frozen legacy file. A readable text event is not proof of correct layout or complete extraction for every document.

- R2: statuses {"empty_retrieval": 5, "ok": 115}; median completed-stage time 15.07s; retrieval requests 242, request errors 2, reported tokens 583,682. Failed query attempts: 2, taking 4.48s excluding endpoint checks and downtime.
- R3: statuses {"empty_retrieval": 4, "ok": 116}; median completed-stage time 15.77s; retrieval requests 246, request errors 3, reported tokens 583,836. Failed query attempts: 3, taking 89.30s excluding endpoint checks and downtime.
- S: statuses {"empty_retrieval": 3, "ok": 117}; median completed-stage time 3.71s; retrieval requests 95, request errors 2, reported tokens 208,738. Failed query attempts: 2, taking 1.05s excluding endpoint checks and downtime.
- D: statuses {"empty_retrieval": 1, "ok": 119}; median completed-stage time 22.88s; retrieval requests 121, request errors 1, reported tokens 1,658,240. Failed query attempts: 1, taking 0.33s excluding endpoint checks and downtime.

All successful requests have matching outbound and returned runtime identifiers. Only technical failures may be retried, with every attempt retained. Empty retrieval is a valid completed miss. Source checks run after retrieval. S/D costs are stage-only, while R1 timing included concurrent source checks; do not interpret these medians as an isolated speed comparison.

Execution spans October 23 and October 25, 2026 (UTC), with network interruptions and resumed process segments. Completed results were retained. Reported request usage excludes unavailable usage from interrupted requests; wall-clock downtime is not retrieval latency. See the execution record and supervisor events for recovery details.

The source-check pool contains 974 distinct unlisted question/source associations: 411 compatible previous decisions and 563 new or upgraded jobs. New source checks used 707 requests and 12,309,020 reported tokens, separate from retrieval. The previously completed baseline source checks are not charged again in this total.

16 source associations received additional direct text or rendered-page review. The decisions and exact evidence are retained in [adjudications](../support_reviews/adjudications.jsonl); original check records remain intact. Usage includes the first source-check pool and the refresh after parser correction, including earlier checks that are no longer needed by the final pool. See the [pool refresh](../parser_correction_review_refresh.json).

## Limits

All questions were already exposed in earlier work. This is descriptive regression testing, not an unseen holdout evaluation. No settings were tuned against these follow-up scores. Snapshot reranking includes cached text for eight documents, but does not test systematic full-text reranking of every candidate. Directory budget, ranking and parsing are isolated comparisons; their combined effect was not tested. No product acceptance threshold or production-scale claim is inferred.

Artifact validation: 74/74 checks passed.

## Artifacts

- [All question scores](questions.csv) and [ordered references](references.csv).
- [Repeated-run agreement](stability.csv), [paired changes](transitions.csv), and [document averages](by_document.csv).
- [Similar-question pairs](pairs.csv), [combined sources](cross_document.csv), and [negative cases](unanswerable.csv).
- [Directory and parser diagnostics](stage_diagnostics.json), [environment verification](environment_validation.json), and [execution record](../EXECUTION.md).
- [Source anchors](../scoring_inputs/standards_with_anchors.json), [page decisions](../scoring_inputs/anchor_adjudications.json), and [validation](validation.json).
- [Plan](../PLAN.md), [execution guide](../README.md), and [machine-readable summary](summary.json).
