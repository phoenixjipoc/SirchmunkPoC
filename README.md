# Sirchmunk document retrieval

This branch evaluates document retrieval using **120 verified questions and 81 raw documents**. Each query returns up to ten ordered files. The tests stop before evidence sampling, final answers or knowledge clusters.

The two objectives are:

1. Retrieve a document containing all required facts, preferably as the first result.
2. Distinguish similar questions that require different issuers, versions or conditions.

## Results

The primary measure uses **98 single-document questions**. The other 22 questions have separate measures.

- Baseline: Top-1 **52.04% (51/98)**, Top-5 **75.51% (74/98)** and Top-10 **81.63% (80/98)**.
- Three repeated runs: Top-1 **45.92%–52.04%**, averaging **50.00%**; 38 questions change between a first-position hit and miss.
- Considering all 81 directory candidates: Top-10 **91.84% (90/98)** and Top-1 **55.10% (54/98)**.
- Legacy-document parser repair: readable text from **81/81** documents instead of 80/81; one additional required source found for XD-16, with no change to single-document Top-1 in the controlled comparison.

Directory coverage and parsing were tested separately. Their combined effect was not measured. These are results on an exposed benchmark, not an unseen test set.

See the [full results](retrieval/followup120/reports/REPORT.md), [per-question scores](retrieval/followup120/reports/questions.csv), [ordered references](retrieval/followup120/reports/references.csv) and [original retrieval baseline](retrieval/reports/basic120/REPORT.md).

## Runtime and configuration

- **LLM:** `gpt-6-sol` for keyword extraction, directory selection and source-support checks. The requested model, outbound request body and response model are checked on every call; a mismatch stops execution. Hit rates and reciprocal ranks are calculated in Python.
- **Runtime:** Sirchmunk `0.0.7` in the `sirchmunk` Docker container, using the [saved source snapshot](retrieval/source_snapshot/). Calls use `/chat/completions` and `stream=false`; the API key and endpoint come from `LLM_API_KEY` and `LLM_BASE_URL`.
- **Generation settings:** temperature, top-p and API seed are not explicitly set. Retrieval calls have no explicit output-token limit. Source checks use JSON responses and `max_completion_tokens=5000`.
- **Search input and output:** all 120 questions search the same 81 originals at `/mnt/docs/S`. Keyword files precede directory suggestions; duplicate paths are removed while preserving order, then the first ten files are returned. Hit@1/5/10 use prefixes of that one list.
- **Keyword search:** two-level keyword extraction with alternative terms, followed by case-insensitive `rga` literal searches; escaped-regex search is the fallback when no matches are found. Search depth is 5 and each search has a 30-second timeout. The tool uses `max_results=20` and five snippet lines per displayed file; the harness reads all logged discovered paths, so 20 is not a cap on file candidates.
- **Directory scan:** depth 8, at most 500 files and up to 800 extracted preview characters per file; the frozen scan contains all 81 originals. R1/R2/R3 randomly select 20 candidates per question for relevance assessment and retain only `high` relevance. D assesses all 81 candidates while keeping R1 keyword results fixed.
- **Repeated runs:** R1, R2 and R3 each cover 120 questions once, with base seeds 17011, 17012 and 17013. Each question uses `base_seed + int(SHA256(question_id)[:8], 16)` for local sampling. These seeds do not make service responses or native file order deterministic.
- **Timeouts and recovery:** 300 seconds per question, 120 seconds per service request, one retrieval worker and a limit of three service requests in flight per process. Client retries are disabled. Follow-up queries allow up to three recorded attempts for technical failures; completed and empty results are retained. Baseline recovery is recorded separately.
- **Parsing and caches:** original PDF/Word files are searched through `rga`, with a local parsing cache. P0/P replay R1 keywords and directory results using fixed file-path order; P alone enables the legacy DOC adapter with `olefile==0.47`. Evidence sampling, knowledge-cluster reuse/construction and final-answer generation are disabled.
- **Source checks:** known verified sources are matched directly. Other returned sources are checked against the required facts and acceptance criteria. New first-ranked sources and proposed positive or uncertain decisions receive a second check using a different prompt with the same model. Positive decisions require both checks to report full support with correct identity and quotations matched to source text, or a recorded source adjudication. Checks use two workers in the baseline and four in the follow-up, with up to twelve quotations per check. Prior decisions are reused only when their inputs and source hashes match.

Exact settings and execution details are in the [baseline configuration](retrieval/inputs/config.json), [follow-up configuration](retrieval/followup120/settings.json), [request guard](retrieval/runtime.py), [source-check worker](retrieval/review_support.py) and [execution record](retrieval/followup120/EXECUTION.md).

## Documents

The [81 originals](poc_docs/S/) are public pension-fund RFPs and industry DDQ/ESG materials: **78 PDF, two DOCX and one legacy DOC**, totaling **47,379,550 bytes (45.18 MiB)**. All have distinct hashes; every PDF has an extractable text layer.

- **PDF length:** 2,546 pages across 78 files; 1-109 pages per file, with a median of 28.5 and a mean of 32.64 pages. Counts come from the original PDF page trees and match the [source inventory](poc/questions/verification/audit_20261014/source_inventory.json).
- **Word length:** saved document properties report 45 pages for the INREV 2022 DOCX, seven for the SAA questionnaire DOCX and 44 for the legacy INREV DOC. These are stored metadata values; Word pagination depends on the rendering environment. All three Word files are excluded from the PDF page total.
- **File sizes:** 12,825-2,825,104 bytes per original (12.52 KiB-2.69 MiB), with a median of 459,895 bytes (449.12 KiB). The 78 PDFs total 45,608,384 bytes, the two DOCX files 559,774 bytes and the legacy DOC 1,211,392 bytes. Sizes refer to the downloaded files, before text extraction; 1 KiB = 1,024 bytes and 1 MiB = 1,048,576 bytes.

There are 34 investment-consultant RFPs, ten investment-manager or outsourced investment-office RFPs, twelve actuarial/audit RFPs, ten custody or retirement-plan service RFPs, four related question-and-answer documents or manager questionnaires, eight DDQ-related documents and three ESG frameworks/FAQs. DDQ materials include templates and supporting notes.

Similar issuers, years and versions are intentional distractors. The [download manifest](poc/corpus/manifest_S.csv) records source URLs, categories, sizes and hashes. Original files are the search input; extracted text supports source verification.

## Questions and scoring

The [verified set](poc/questions/questions_verified.csv) contains 50 detail questions, 18 medium questions, 30 questions forming 15 similar-wording pairs, 13 broad questions and nine negative questions.

The detail, medium and paired questions form the 98 single-document cases. The broad questions comprise twelve required-source combinations and one thematic question. Negatives report returned suggestions without a refusal score.

For a single-document question, **Hit@k** is one when at least one of the first k files contains all mandatory facts for the correct issuer, version and conditions. **MRR@10** uses the reciprocal rank of the first qualifying file, or zero if none appears within ten. Similar pairs also track whether the opposite question's exclusive source ranks first. Combined-source questions measure required-source coverage.

Reference facts and acceptance criteria are used only for source assessment. Retrieval receives questions without expected answers or source labels. The [question audit](poc/questions/verification/verification_report.md) supported 109 references and corrected eleven. Unlisted returned sources receive separate support checks. See the [scoring rules](retrieval/PLAN.md#scoring) and [follow-up plan](retrieval/followup120/PLAN.md).

## Workflow and files

Queries use keyword discovery and directory selection, followed by an ordered, deduplicated file list. The baseline keeps keyword files first; the follow-up isolates repeatability, directory coverage and parsing. Source checks and scoring run separately from retrieval.

- `poc_docs/S/`: original search documents.
- `poc/corpus/`: download records and corpus preparation.
- `poc/questions/`: the 120-question dataset, its drafts and supporting source audit.
- `retrieval/`: baseline scripts, frozen inputs, execution records, source checks and results.
- `retrieval/followup120/`: repeated runs, controlled comparisons, raw records and final reports.
- `retrieval/source_snapshot/`: unchanged installed-package snapshot used for source-hash verification; it is not a separate experiment.

The dataset paths remain stable so the frozen input hashes and validation scripts remain reproducible.

## Reproduction and validation

Install host dependencies from the single [requirements file](requirements.txt). Follow the [baseline execution guide](retrieval/README.md#reproduce) and [follow-up guide](retrieval/followup120/README.md#reproduction) for new runs. Runtime credentials stay outside the repository.

The saved results can be validated without service requests:

```bash
python retrieval/validate.py
python retrieval/followup120/validate.py
```

The [execution record](retrieval/followup120/EXECUTION.md) retains recovery details. The [parser correction record](retrieval/followup120/PARSER_CORRECTION.md) explains the excluded first attempt and corrected replay. See the saved validation report for the current checks.
