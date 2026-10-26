# Top-five and top-ten reranking

## Objective and scope

Measure whether reranking improves first-document support, whether ten candidates outperform five, and the added request cost and time. Reuse the same 120 questions, 81 originals and frozen R1 candidate lists. Produce ordered references only.

## Arms

- Baseline: unchanged R1, with at most ten references.
- RR5: reorder positions 1-5 and leave positions 6-10 unchanged.
- RR10: reorder positions 1-10.

Run each new arm once on all 120 questions. Empty and single-candidate lists need no request. The first question is the smoke check and remains part of the final run. Alternate arm order between consecutive questions. All ranking requests run serially; source checks follow afterward.

## Inputs and controls

Use only the question, opaque document identifiers, filenames, titles, keywords and existing previews capped at 800 characters per document. Exclude cached full content, original ranks and source labels. Shared documents have identical fields in both arms. Order candidate inputs by a fixed hash of seed, question identifier and filename; common candidates retain the same relative presentation order.

Freeze corpus, baseline, payloads, code, prompt and settings before requests. Use the existing guarded service client and inspect outgoing and returned identifiers on every request. Exact service settings are in settings.json. A mismatch stops the campaign.

Require a complete, duplicate-free permutation of supplied identifiers. Retry only technical failures, at most three recorded attempts per task. On exhaustion, preserve the original order and label the fallback. Retain completed results on resume. Stop on authorization, configuration or runtime-identity failures. A failed recovery check pauses subsequent tasks.

## Scoring

Use 98 single-document questions for Hit@1/5/10 and MRR@10. A source must contain all mandatory facts with correct identity, edition and conditions. Reuse compatible source-grounded decisions. Newly first-ranked unlisted sources need two checks or a recorded source adjudication. Apply the same final support labels to all three arms. Report unresolved support as score bounds.

Report gains and losses against the baseline and between RR5/RR10. Report fifteen similar-question pairs, first-position opposite-source confusion, twelve required-source combinations, one thematic example set and nine negative suggestion cases separately. Negative cases have no refusal score.

The candidate sets stay fixed: all three Hit@10 values must match, and RR5 Hit@5 must equal baseline Hit@5. With current labels, the first-position ceilings are 74/98 for RR5 and 80/98 for RR10. Label corrections require rescoring every arm.

## Delivery and limits

Save all payloads, calls, attempts, ordered references, source decisions, per-question scores and an English report. Separate ranking, preflight and source-check usage; report ranking median and p95 latency. Do not compare this stage-only timing with the historical full-search timing.

This exposed benchmark and one pass per arm measure a controlled regression, not unseen generalization or run-to-run stability. The preview limit can hide relevant evidence. Retrieval discovery, parsing and directory budgets remain unchanged. No final answers or knowledge clusters are produced.
