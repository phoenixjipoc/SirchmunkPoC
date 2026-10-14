# Test methodology

## Research questions

The first question is answer correctness over raw RFP/DDQ documents. The second is whether similar questions with different correct answers cause inappropriate reuse of earlier knowledge clusters. Accuracy is measured separately for all questions, question types, the predefined pairs, and actual reuse hits.

## Corpus and parsing

The corpus contains 81 public files: 78 PDFs, two DOCX files, and one legacy DOC. The original bytes are under `poc_docs/S/`; public sources are listed in `poc/corpus/candidates.csv` and `manifest_S.csv`. Files were copied into Docker at `/mnt/docs/S`. They were not converted to Markdown as the search corpus.

The preflight checked document SHA-256 values against the question audit, nonempty extraction, control characters, and keyword-search text availability. This is a parsing sanity check, not a guarantee of faithful table/layout extraction.

Two extraction paths are used by the installed library:

| Purpose | Parser |
|---|---|
| Keyword search and candidate discovery | `rga`; PDF adapter uses Poppler `pdftotext`, DOCX adapter uses Pandoc |
| Candidate reading for evidence sampling | Sirchmunk `fast_extract()` calls Kreuzberg `extract_file()` and passes `ExtractionResult.content` to `MonteCarloEvidenceSampling` |

The inspected Kreuzberg version was 4.8.2. The parser operates locally; model calls occur during query interpretation, evidence extraction/reasoning, and answer generation. The test did not build a separate full-corpus vector-chunk index. Query embeddings are nevertheless used for knowledge-cluster similarity lookup when reuse is enabled.

All three runs used the same prewarmed rga text cache, `/poc_cache/rga_S`. Each stage's `.cache/rga` points to that cache. **Shared parsed text is not shared knowledge-cluster memory.** Knowledge stores were separate and initially empty. Parsing prewarm and C's embedding-model preload occurred outside timed questions.

The PDFs have extractable text layers. This experiment did not evaluate a scanned-only OCR corpus. The older INREV DOC produced 63,927 characters with substantial mojibake and 240 replacement characters; rga returned only a binary match. It was retained unchanged for all runs. Independently recovered audit text was used to verify references, not substituted into the search corpus.

## Reference-question verification

The 120 questions were frozen before the new experiment. Three independent AI reviewers each blind-answered a disjoint batch of 40 questions, then compared their saved answers with the original references. A coordinating reviewer checked disagreements against the original sources. Each question therefore had one blind reviewer, not three separate blind reviews.

109 original references were supported and 11 were corrected; six questions also had their scope clarified. The audit preserves initial blind answers, including mistakes found later. AI agreement does not establish a human-certified gold standard. See the verification report for the individual corrections and the LAFPP exception missed by both an initial reference and its blind answer.

The final question mix is 50 detail, 15 pair-A, 15 pair-B, 18 medium, 13 broad/cross-document, and nine unanswerable questions. Every pair-A immediately precedes its pair-B. There are 120 unique question strings.

## A, B, and C configuration

| Setting | A | B | C |
|---|---|---|---|
| Mode | DEEP | DEEP | DEEP |
| `top_k_files` | 10 | 5 | 10 |
| Cluster reuse | Disabled | Disabled | Enabled |
| Similarity threshold | 0.85 | 0.85 | 0.85 |
| Initial clusters | Empty | Empty | Empty |
| Question count/order | Same 120 | Same 120 | Same 120 |

Common runtime: Sirchmunk 0.0.7 and configured model `gpt-5.4`. The image and digest are saved in every run's `run_meta.json`; the experiment image is `modelscope-registry.us-west-1.cr.aliyuncs.com/modelscope-repo/sirchmunk:ubuntu22.04-py312-0.0.7`.

C's effective embedding model was `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`, dimension 384, with a 12.5-second preload outside the question timers. Defaults included maximum loops 10, token-budget parameter 128,000, maximum depth 5, directory scanning enabled, context return enabled, fallback disabled, a 600-second question timeout, and cluster similarity top-k 3. The token budget is a runtime parameter, not a strict cap on usage after parallel operations or retries. No seed or temperature override was supplied.

Questions were serial. Library operations within a question can run concurrently. Each stage used `/poc_runs/20261014_ABC_verified120_<A|B|C>/work`. No search model received the reference answer: the container's `questions.jsonl` contains only IDs and question text.

## Execution path

`run_eval.py` invokes the container-side `harness/sirch_runner.py` via `docker exec`. The runner constructs `AgenticSearch` and calls its Python `search()` method. Sirchmunk calls the configured model API internally. This experiment **did not call the Sirchmunk HTTP `/api/v1/search` endpoint**, exercise its web UI, or establish HTTP end-to-end availability.

The runner observes candidate files, sampled files, evidence-found files, final citations, reuse IDs/queries, answer-gate decisions, latency, usage, warnings, and errors. Wrappers observe library calls without changing the search algorithm. Successful `llm.achat` response usage includes sampling subcomponents; older experiments used a narrower accounting method.

DEEP still includes intent routing. In each run two questions took the direct-document path. Its default collector takes at most five files, independently of `top_k_files`; CONS-16 read unrelated files instead of the ten named RFPs. Synthetic `DS` answer wrappers are not proof of a document-summary route. Installed source excerpts and raw logs are included.

## Grading and review

The primary judge received the full answer, frozen reference answer, supporting passage, and acceptance criteria. It used the same configured `gpt-5.4` model as search. Labels are `correct`, `correct_refusal`, `partial`, `wrong`, `hallucinated`, `no_answer`, and `error`.

- Overall correctness is `(correct + correct_refusal) / 120`.
- Partial answers do not count as correct; errors and refusals stay in the denominator.
- `no_answer` identifies the fixed no-results response. Other refusals to answer an answerable question can be labeled `wrong` under the frozen rubric.
- `hallucinated` is the label for an unsupported concrete answer on a negative question. A zero count for this label does not imply that all other answers were factually correct.
- File coverage measures the fraction of known reference files reached per question, not whether the required fact is actually supported.

All initially non-correct results and a reproducible approximately 20% sample of initially correct/refusal results were selected for review: 190 records in total. A separate same-model request withheld the primary label; exact no-results/errors were checked deterministically. The coordinating AI reviewed additional cases, all nine reuse hits, and all disagreements. Final decisions are separate from original judge and secondary-review records. This reduces some grading mistakes but does not remove same-model bias or semantic judgment.

## Repairs and limitations

- A's cluster export failed when Python `splitlines()` split JSON content on U+2029. The export parser was repaired to split on LF; Unicode content was preserved through escaped JSON. Search and judging were not rerun. Original/fixed script hashes and the regression check are saved.
- C / SVC-03 recovered from a connection failure through an automatic phase retry. Its 137.83 seconds and 148,219 tokens were retained.
- A/B/C had 5/2/3 return-object serialization failures respectively; answers were recovered and graded. These are not HTTP availability results.
- SVC-15 does not distinguish financial from actuarial audit services. Main scores retain the frozen reference; the English sensitivity table excludes that one ambiguous question as a secondary view.
- Timing excludes prewarm, judging, review, and export. API-internal failed retries may not return countable usage. Token counts are reported without guessed monetary costs.
- A single pass, 15 deliberately selected pairs, and nine negative questions do not prove statistical significance, production suitability, or behavior at 1,000-2,000 documents.
- Identical-question replay and genuinely beneficial reuse were not demonstrated by this experiment.

All evidence-preservation and translation checks for this English repository are separate from the original evaluation's `validation.json`.
