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

## Documents

The [81 originals](poc_docs/S/) are public pension-fund RFPs and industry DDQ/ESG materials: **78 PDF, two DOCX and one legacy DOC**, totaling **47,379,550 bytes (45.18 MiB)**. All have distinct hashes; every PDF has an extractable text layer.

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
