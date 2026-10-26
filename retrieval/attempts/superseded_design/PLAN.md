# Retrieval benchmark

This campaign measures source retrieval, using the existing 81 original documents and 120 verified questions. It does not produce final answers or create, read or reuse knowledge clusters.

## Frozen design

- R10 selects up to ten files; R5 selects up to five. Both use the DEEP keyword, directory and evidence retrieval components.
- Each configuration runs all 120 questions three times: 720 queries in total. The three base seeds are 17011, 17012 and 17013. A question-specific seed is shared between corresponding R5 and R10 runs.
- Repetitions run one at a time, with configurations alternating across repetitions. Each process handles questions sequentially and permits at most three simultaneous remote calls. Sampling interleaving can vary; seeds do not guarantee identical results. The initial six-process launch exhausted container memory before any query completed; its logs are retained under `attempts/parallel_start`.
- Each query has fresh retrieval state. Only immutable parsed document text is shared. Keyword caches have separate per-query paths. No prior query, answer, standard or cluster is supplied to retrieval.
- Configuration, query order, acceptance rules, original document hashes, extracted text and installed source hashes are saved before execution. Original files remain the retrieval inputs.

## Retrieval boundary

The adapter calls the installed keyword extraction, keyword search and directory ranking methods. Directory ranking randomly samples twenty candidates when more are available; only high-relevance results are added. The native merge order is keyword hits first, then directory hits, with duplicates removed. This operational order defines the returned ranks.

The selected files use the installed parser and evidence sampler. Documents below 100,000 extracted characters return their complete text. Larger documents use the existing fuzzy/random probes, three rounds, score-eight early stopping and up to five accepted probes scoring at least four. Each accepted probe expands to the existing 2,000-character context window. The adapter returns those exact windows instead of generating a summary. Low-scoring fallback probes remain visible with their unsuccessful status.

Direct-document answer generation, answer-dependent search loops, evidence summaries, final answers, specification memory and cluster persistence are excluded. This is a retrieval-only adaptation of DEEP, not an unchanged end-to-end DEEP run. Reference rank is fixed before parsing; a failed first file is not silently replaced by the next one.

## Assessment

The set contains 50 detail, 18 medium, 13 broad, 30 paired and nine unanswerable questions. The 30 paired questions form fifteen pairs. The 111 answerable questions contain 98 single-source questions and thirteen questions listing multiple sources.

For the 98 single-source questions, Document Hit@1/5/10 requires a returned document containing the required facts with the correct entity, edition, dates and conditions. The previously verified source is a confirmed positive, not proof that every other file is negative. Unlisted returned documents receive a support review. A partial or merely related document does not count. Hit@10 is available only for R10.

Multiple-source questions are reported separately. Source coverage measures retrieval of the required source set; complete support requires the whole necessary combination. Optional contextual sources are excluded from the required set. The thematic DDQ synthesis uses coverage of its verified examples as a descriptive measure, not an exhaustive relevance set. A single document is not credited with a cross-document comparison merely because it contains one component fact.

Evidence sufficiency concerns only the exact returned text, independently of document identity. For confirmed sources returned in full, verified supporting facts can be checked against the frozen parsed text. For sampled passages and unlisted sources, two independent assessments use the question, acceptance rule and supplied text, without seeing configuration, rank, run or the other assessment. Supporting quotations must occur in the supplied text. Disagreements and ambiguous scope remain explicit until resolved. Assessment output is a support classification and quotations, never a proposed answer.

The nine unanswerable questions are reported separately: related background is not a false positive by itself. The sampler's small-file score of ten is an automatic full-text shortcut, not calibrated answerability confidence. Report its positive statuses as retrieval behavior, not as generated false answers or correct refusals. Evidence that appears to answer a negative question receives a scope review.

For each similar-question pair, report correct-source hits, opposite-question source contamination and sufficient evidence. Shared documents are not automatically mistakes; edition and entity distinctions control the assessment.

Errors stay in the denominators. Missing or unresolved evidence is reported as unknown with lower/upper bounds where relevant. Empty retrieval, parser failure, sampling failure and model mismatch have separate statuses. Scores are descriptive baselines; no product acceptance threshold is invented.

## Runtime controls and outputs

Every request explicitly selects the configured model. The outbound HTTP body and raw response model are checked. A mismatch writes a shared stop marker and prevents further calls. A live preflight precedes execution. Transport uses non-streaming responses so every raw response can be checked before wrapper fallback logic; prompt and retrieval logic remain unchanged. Retries are disabled to make failed calls visible.

Outputs include configuration and source manifests, per-query candidate order and raw evidence, request/response model records and token counts, assessment decisions, pair comparisons, error details and aggregate results. Latency includes concurrency contention and excludes one-time parser warmup. Report token usage rather than an unsupported cost estimate.
