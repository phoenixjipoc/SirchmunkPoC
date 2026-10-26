# Basic retrieval test

The objective is to retrieve a document containing the complete supporting facts as the first result. The campaign uses 81 original documents and all 120 verified questions once. Each query returns at most ten ordered files. Top-1, Top-5 and Top-10 are calculated from that same list.

## Scope

The set has 98 single-document questions, twelve questions requiring source combinations, one thematic question and nine unanswerable questions. Fifteen similar-question pairs are already included in the 120 questions.

The adapter uses DEEP keyword extraction, keyword search and directory selection, then stops at the ordered document list. It does not sample evidence, summarize documents, generate final answers, or create/read/reuse knowledge clusters. It is a document-retrieval adaptation, not a full end-to-end DEEP run.

## Execution

- Run one process, all 120 questions in the frozen order, with up to ten returned files per query. No result-based retries or tuning. Technical failures may be recovered after a successful endpoint check; preserve failed attempts and never rerun a completed query to improve its score.
- Pin the configured runtime and base seed. Compare the identifier in each outbound request with the raw response; stop on a mismatch. Non-streaming transport allows validation before wrapper fallback logic.
- Freeze document hashes, questions, acceptance rules, source code hashes and directory metadata before execution. Benchmark input files contain no standard answers or source labels.
- Share only document parsing caches and immutable directory metadata. Every query gets fresh keyword, ranking and search context. Parsing caches contain document text, not previous answers or rankings.
- Preserve native candidate order: keyword-discovered files first, then high-relevance directory files, removing duplicates. Directory selection retains the installed random twenty-file sample. This native operational order defines the returned ranks.
- Record all candidates before truncation, the returned ten, keyword logs, directory inputs, call records, errors and elapsed time. Latency excludes cache warmup and includes both discovery paths.

## Scoring

For the 98 single-document questions, Document Hit@k is one when at least one of the first k files contains all mandatory facts for the correct entity, edition, date and conditions. The verified source is a confirmed positive. Other returned files are checked for equivalent support rather than automatically declared wrong. Related subject matter or a matching number alone does not qualify.

The twelve cross-document questions use required-source coverage and complete-set retrieval at 1, 5 and 10. Optional contextual sources are excluded. DDQ-11 is a thematic synthesis with non-exhaustive examples: report example-source coverage separately, not a claim of exhaustive recall. Do not include these thirteen questions in the single-document Top-1 denominator.

The nine unanswerable questions retain their prior corpus-level findings. Report returned background documents and entity/version confusion separately. A nonempty document list is not itself a false answer. This retriever has no calibrated answerability decision, so do not report correct-refusal accuracy.

Verified sources use the completed source audit. Other returned documents receive a separate support check against their complete, whitespace-normalized original-derived text. The check sees the question, acceptance rule and document, but not rank, run or another verdict. First-position exceptions and all proposed additional positives receive a second independent request. Quotations must match the supplied text. Conflicts remain unresolved until source-grounded adjudication. These checks run separately from retrieval and never feed back into it; their concurrent activity can affect observed latency.

For each similar-question pair, report each side's Top-1/5/10 support and whether the opposite question's exclusive source was retrieved. Shared sources alone do not imply confusion. Separate first-place confusion from a distractor appearing later.

Errors remain in the relevant denominators. Unknown support assessments are explicit and produce lower/upper bounds instead of being silently dropped. Report counts with percentages. This one-run baseline does not measure repeated-run stability or establish a product acceptance threshold.

## Deliverables

Save frozen inputs, runtime checks, all 120 ordered results, per-question scores, required-source coverage, pair comparisons, unanswerable cases, support decisions, token usage and an English summary. Keep the superseded multi-round launch records separate from this test.
