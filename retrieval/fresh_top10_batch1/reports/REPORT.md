# Fresh Top-10 retrieval and reranking: batch 1

A single new retrieval pass searched the same 81 original documents for all 120 questions. Reranking then reordered each newly returned list of at most ten candidates. Historical candidate lists were not reused.

## Results

Primary measures use 98 single-document questions. A hit requires complete supporting facts for the correct identity, version and conditions.

- Fresh retrieval: Hit@1 **52.04% (51/98)**; Hit@5 75.51% (74/98); Hit@10 79.59% (78/98); MRR@10 0.6194.
- After Top-10 reranking: Hit@1 **77.55% (76/98)**; Hit@5 79.59% (78/98); Hit@10 79.59% (78/98); MRR@10 0.7810.

Reranking adds 25 first-position hits and loses 0, a net change of +25.51 percentage points. Candidate membership and Hit@10 stay unchanged for every question.

## Remaining misses

- empty_retrieval: 6.
- support_present_but_not_first: 1.
- technical_rerank_fallback: 1.
- verified_source_absent_from_candidates: 8.
- verified_source_beyond_cutoff: 6.

Candidate-absence categories refer to audited sources; files outside the returned ten were not exhaustively assessed. See [miss details](misses.csv).

Of the 22 remaining first-position misses, 20 have no fully supporting file in the returned ten. CONS-07 has a supporting file at rank 3 after reranking. CONS-08 retained its original rank 5 after three connection errors; it is a technical fallback, not a completed ranking decision.

## Similar questions and other cases

- Fresh retrieval: both questions hit first in 2/15 pairs; an opposite question's exclusive source ranks incorrectly first on 3/30 paired queries.
- Fresh retrieval, first 5: required-source sets complete for 1/12 questions, mean required-source coverage 35.42%; thematic example coverage 3/6.
- Fresh retrieval, first 10: required-source sets complete for 2/12 questions, mean required-source coverage 44.58%; thematic example coverage 3/6.
- Reranked: both questions hit first in 9/15 pairs; an opposite question's exclusive source ranks incorrectly first on 0/30 paired queries.
- Reranked, first 5: required-source sets complete for 2/12 questions, mean required-source coverage 44.58%; thematic example coverage 3/6.
- Reranked, first 10: required-source sets complete for 2/12 questions, mean required-source coverage 44.58%; thematic example coverage 3/6.

The nine negative cases report suggestions without an answerability or refusal score.

## Question types

- Fresh retrieval: detail 28/50; medium 9/18; pair_a 7/15; pair_b 7/15.
- Reranked: detail 40/50; medium 13/18; pair_a 13/15; pair_b 10/15.

## Execution and usage

- Fresh retrieval: 120 tasks; statuses {'ok': 114, 'empty_retrieval': 6}; 244 requests, 2 request errors and 580,908 reported tokens. Per-task median 14.147s and p95 19.989s.
- Reranking stage: 120 tasks; statuses {'ok': 94, 'skipped_single': 19, 'skipped_empty': 6, 'fallback_original': 1}; 97 requests, 3 request errors and 160,018 reported tokens. Per-task median 2.981s and p95 4.921s.

Source checking was separate: 74 requests, 1,633,490 tokens and 72 new or upgraded associations; 402 compatible decisions reused. Preflight used 9 requests and 101 reported tokens.

Two checks contained unmatched quotation fragments. Inspection of the saved source text confirmed both negative decisions; exact quotations and offsets are saved in support_reviews/adjudications.jsonl. No primary score remains unresolved.

Stage timings exclude metadata scanning, parsing warmup, source checking and downtime. P95 uses the nearest-rank method. Ranking tasks with zero or one candidate have no remote request. Paired total latency is the retrieval time plus its reranking time; the reranking stage alone is not a replacement for retrieval cost.

Transport interruptions required 3 checkpointed resumes. The checkpoints protected 41, 96, 200 completed results respectively. Only unfinished tasks resumed; completed results and settings were retained. Failed attempts remain in the call and attempt records.

## Configuration and limits

Native retrieval retained the twenty-file directory sample, fresh keyword extraction and search, keyword-first merge and ten-file cutoff. A new directory snapshot and isolated parsing cache were created. Reranking used identical filenames, titles, keywords and previews capped at 800 characters, with fixed shuffled presentation and hidden original ranks. Runtime identifiers were verified on requests and responses.

The first native result was saved successfully, but copying its in-memory log into the batch record failed on a datetime value. A serialization-only repair preserved that completed result without another request. Original code, changed hashes and the recovered result are recorded in execution_repair/.

The native legacy DOC parser remains limited: a warmup binary-match message is not readable document text. No parser repair or expanded directory budget was applied. No final answers, evidence sampling or knowledge clusters were produced.

One exposed batch measures the paired change for its own candidates; it does not establish stability or unseen performance. Fresh candidate membership can differ from earlier runs. Source checks and ranking are separate, and any scoring uncertainty must remain explicit.

## Files

- [Plan](../PLAN.md), [settings](../settings.json), [configuration](../inputs/config.json) and [execution repair](../execution_repair/revision.json).
- [All 240 scores](questions.csv), [references](references.csv), [paired changes](transitions.csv) and [remaining misses](misses.csv).
- [Similar pairs](pairs.csv), [combined sources](cross_document.csv), [negative cases](unanswerable.csv) and [document averages](by_document.csv).
- [Summary](summary.json), [validation](validation.json) and [source-check manifest](../review_inputs/manifest.json).
