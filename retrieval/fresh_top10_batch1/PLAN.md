# Fresh Top-10 retrieval and reranking: batch 1

Run one batch on all 120 questions and 81 originals. First execute fresh document retrieval, then rerank the same newly returned candidates. Compare the two lists before and after reranking. Historical candidate lists are not inputs.

## Controls

Keep the existing native retrieval configuration: fresh keyword extraction and search, twenty sampled directory candidates per query, keyword-first merge and a ten-file cutoff. Use the original base seed, a newly scanned metadata snapshot and a new isolated parsing cache. The current native parser remains unchanged. This batch measures a fresh run plus the effect of reranking; it does not change recall settings.

After all retrieval tasks finish, freeze their results and prepare reranking payloads. Use the existing prompt, service settings and fixed presentation order. Supply the question, document identifier, filename, title, keywords and at most 800 preview characters. Hide original ranks and source labels. Require an exact permutation of the returned files. Empty and single-candidate lists are retained without a ranking request.

Pin the runtime and check outgoing and returned identifiers on each successful request. Freeze code and inputs before execution, metadata before retrieval, and candidate results before reranking. No final answers, evidence sampling or knowledge clusters are produced.

## Recovery

Allow at most three attempts per task for technical failures. An unsuccessful connection check stops subsequent work until recovery. Retain completed tasks on resume and never retry them to improve a score. Exhausted retrieval failures return an empty marked result; exhausted ranking failures retain the original order. Keep all failures in their respective denominators.

## Scoring and delivery

Use identical final source-support labels for both arms. Reuse compatible audited decisions; check newly returned sources and upgrade first-position exceptions. Full support requires all mandatory facts and correct identity, version and conditions. Resolve uncertain or conflicting decisions against source evidence. Source checking starts after ranking completes.

Report Hit@1/5/10 and MRR@10 on the 98 single-document questions, along with per-question gains and losses. Report fifteen similar-question pairs, twelve required-source combinations, one thematic case and nine negative cases separately. Candidate membership and per-question Hit@10 must remain unchanged between arms. Keep unresolved scores explicit.

Save raw requests, attempts, full candidate lists, ordered references, scoring decisions, stage costs and an English report. Compare fresh retrieval with its own reranked output. One exposed batch does not establish stability or unseen performance.
