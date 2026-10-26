# Basic document retrieval results

**Document Hit@1: 51/98 (52.04%).** Hit@5: 74/98 (75.51%). Hit@10: 80/98 (81.63%).

One pass covered all 120 questions against 81 original documents. Each query returned up to ten ordered files. The three cutoffs use the same results; they are not separate runs. No final answers, evidence summaries or knowledge clusters were produced.

## What the result means

The primary denominator is the 98 single-document questions. A hit requires a document containing the mandatory facts for the correct issuer, edition and conditions. Verified sources use the completed source audit; other returned files receive separate checks against their original-derived text. This measures document retrieval, not whether a selected excerpt or generated answer is sufficient.

The twelve source-combination questions, one thematic question and nine unanswerable questions are separate. Execution statuses: empty_retrieval=3, ok=117. Errors remain in denominators.

## Single-document categories

- detail: Top-1: 28/50 (56.00%); Top-5: 41/50 (82.00%); Top-10: 44/50 (88.00%).
- medium: Top-1: 9/18 (50.00%); Top-5: 12/18 (66.67%); Top-10: 15/18 (83.33%).
- pair_a: Top-1: 8/15 (53.33%); Top-5: 11/15 (73.33%); Top-10: 11/15 (73.33%).
- pair_b: Top-1: 6/15 (40.00%); Top-5: 10/15 (66.67%); Top-10: 10/15 (66.67%).

## Similar questions

The fifteen pairs are included in the 120 questions. Both sides found supporting sources at rank one in 3/15 pairs, within five in 8/15, and within ten in 8/15. The opposite question's exclusive source appeared incorrectly first in 2 of the thirty paired queries.

An opposite source appearing later is recorded as a distractor, not automatically an error. A shared file is not automatically confusion. See [pair details](pairs.csv).

## Cross-document coverage

- Top-1: complete verified source sets for 0/12 questions; mean source-set coverage 13.82%.
- Top-5: complete verified source sets for 1/12 questions; mean source-set coverage 32.50%.
- Top-10: complete verified source sets for 2/12 questions; mean source-set coverage 40.83%.

For the thematic DDQ question, Top-10 found 3/6 verified example sources. Its examples are not an exhaustive relevance set. Source-set coverage is not proof that every possible minimum evidence combination has been enumerated. See [coverage details](cross_document.csv).

## Unanswerable questions

9/9 negative questions returned documents. Those suggestions can be background material. The retriever does not assert an answer or make an answerability decision, so this is neither a false-answer rate nor a correct-refusal rate. The prior absence findings and returned files are preserved in [unanswerable cases](unanswerable.csv).

## Failure analysis

- No files returned: 3 questions.
- Supporting file ranked 2–5: 23 questions.
- Supporting file ranked 6–10: 6 questions.
- Verified source absent from discovered candidates: 11 questions.
- Verified source found beyond the ten-file cutoff: 4 questions.

INV-12 illustrates the distinction between document similarity and support. Its first result was `IMRF__sample-investment-consulting-rfp.pdf`; the verified source is `IMRF__sample_investment_manager_rfp.pdf`. The question asks about investment-manager evaluation, so consulting requirements are not interchangeable. Its Top-1/5/10 outcomes are miss / hit / hit.

The installed merge places keyword hits before high-relevance directory suggestions. Directory selection also samples twenty of the 81 files. These properties can explain poor first-position ordering or incomplete candidate discovery; this run does not isolate their individual causal effects.

## Runtime and source checks

All 310 retrieval call attempts were recorded: 241 successful responses and 69 errors. Identity checks for successful responses passed. There were 189 keyword requests and 121 directory requests, including failed and recovered attempts. Exact runtime identifiers, source hashes and image digest are in the [runtime records](../../results/basic120/preflight.json) and [environment record](../../runtime_environment.json).

A connection interruption required technical recovery of 69 queries. The 51 previously completed results were retained unchanged. Failed attempts remain in the archive and call totals; the baseline contains one completed result per question, not one network attempt per question. No semantic failure was retried to improve its score.

Median completed-query time was 13.81 seconds. The sum of completed-query times was 29.15 minutes. Reported retrieval usage was 407,819 input and 175,513 output tokens; failed calls without usage data cannot be assigned a token cost. Cache warmup, interruption time and source verification are separate. Concurrent source checks may affect timing, so latency is an observation rather than an isolated performance comparison.

Separate checks covered 473 unlisted returned documents using 521 requests. They confirmed 0 additional supporting source associations. Reported verification tokens: 10,417,650. Every proposed additional positive and unlisted first result receives two separate requests; the two checks use the same configured service and are not independent proof. 11 quotation-format discrepancies were resolved using exact source passages or a saved original-page image; see [adjudications](../../support_reviews/adjudications.jsonl).

Parser validation found readable keyword text in 80/81 originals. The legacy INREV DOC returned byte matches rather than normal text. It is a verified source for cross-document question XD-16; it remained in the corpus and was not converted or excluded. This limitation is distinct from whether the original file itself contains the required facts. See [parser validation](../../results/basic120/parser_validation.json).

## Limits and artifacts

This is a single-run baseline. It does not measure repeated-run stability, answer generation, cluster reuse, excerpt quality or calibrated refusal. No product acceptance threshold is inferred. Earlier aborted starts are archived and excluded.

- [All 120 question scores](questions.csv)
- [Ordered references and support decisions](references.csv)
- [First-position failures](failures.csv)
- [Machine-readable summary](summary.json)
- [Artifact validation](validation.json)
- [Plan](../../PLAN.md) and [reproduction guide](../../README.md)
- [Execution record](../../EXECUTION.md)
