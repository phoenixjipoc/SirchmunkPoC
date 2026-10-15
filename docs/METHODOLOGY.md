# Test methodology

## Scope and configuration

The campaign uses 81 original documents and the same 120 verified questions in the same order. All runs use DEEP mode and Sirchmunk 0.0.7.

| Run | Evidence-file limit | Cluster reuse | Similarity threshold |
|---|---:|---|---:|
| A | 10 | Off | 0.85 |
| B | 5 | Off | 0.85 |
| C | 10 | On | 0.85 |

Each stage starts with an empty cluster store at `/poc_runs/20261014_ABC_verified120_<A|B|C>/work`. C can reuse only earlier C clusters. Questions run serially; operations within a question can run concurrently.

Exact service settings, container image/digest, and code hashes are recorded in [campaign.json](../poc/results/20261014_ABC_verified120/campaign.json) and each stage's `run_meta.json`. Common limits are ten loops, 128,000 tokens, depth five, and 600 seconds per question. The token setting is not a strict usage cap after parallel work or retries. No seed or temperature override was supplied.

## Parsing and search

Original PDF/DOCX/DOC files are copied to `/mnt/docs/S`; no Markdown conversion is used as search input.

| Purpose | Implementation |
|---|---|
| Keyword search | `rga`: Poppler `pdftotext` for PDF; Pandoc for DOCX |
| Candidate reading | `fast_extract()` through Kreuzberg 4.8.2 |
| Evidence selection | Monte Carlo evidence sampling |

All stages share the prewarmed text cache `/poc_cache/rga_S`. Cluster stores remain separate. Parsing prewarm and C's 12.5-second similarity-service preload are outside question timings. No full-corpus vector-chunk index was built; cluster lookup uses semantic similarity.

Every PDF has extractable text. Scanned-only OCR was not tested. The legacy INREV DOC produced 63,927 characters with 240 replacement characters, and `rga` returned a binary match. Its handling remained unchanged across A/B/C. Separately recovered audit text was not substituted into search.

## Execution and evidence

`run_eval.py` invokes `harness/sirch_runner.py` through `docker exec`. The runner calls `AgenticSearch.search()` directly and records answers, candidates, evidence, citations, reuse IDs, gate decisions, timing, usage, and errors. Search receives only IDs and questions. The HTTP API and web UI were not tested.

Two questions per stage took a direct-document route with its own five-file default. CONS-16 consequently missed the ten named RFPs. Usage includes successful service responses from sampling subcomponents; failed calls without returned usage may be uncounted.

## Verification and scoring

Three separate automated review sessions blind-answered 40 questions each before comparing references. Source adjudication supported 109 references, corrected 11, and clarified six question scopes. Initial blind answers remain preserved.

Answers were scored against the frozen reference, supporting passage, and acceptance criteria. Search and scoring used the same configured service, so separate requests may share errors. The required queue covered initially non-correct answers and about 20% of initially correct/refusal answers: 190 records, all resolved. Secondary review withheld the primary label; final decisions remain separate from initial records.

Accuracy is `(correct + correct_refusal) / 120`. Partial, wrong, no-answer, and error cases stay in the denominator. See [workflow and grading](EVALUATION.md) for labels and examples.

## Limits and repairs

- A's Unicode JSONL export was repaired without rerunning search or grading.
- C/SVC-03 recovered from a connection failure; 137.83 seconds and 148,219 tokens remain recorded.
- A/B/C had 5/2/3 serialization recoveries, with no unrecovered runtime errors.
- SVC-15 has an ambiguous audit scope; a separate sensitivity table excludes it.
- File coverage does not establish that the required fact was found. Missing citation traces are reported separately.
- Timings exclude preparation, scoring, review, and export.
- One pass, 15 selected pairs, and nine negative questions do not establish production performance or identical-question replay benefits.
