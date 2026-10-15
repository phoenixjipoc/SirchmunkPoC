# Sirchmunk PoC: answer accuracy and similar-question robustness

This repository contains the public document corpus, evaluation questions, verification records, harness, execution history, and results for the verified 120-question Sirchmunk proof of concept. It investigates two questions:

1. **How accurately does Sirchmunk answer questions from raw RFP and DDQ documents?**
2. **When questions look similar but require different answers, does knowledge-cluster reuse preserve the correct institution, document version, and requested fact, or mistakenly reuse an unsuitable answer?**

The principal experiment was completed: **81 original documents, 120 source-verified questions, and three sequential DEEP runs (360 evaluations)**. The tested library was **Sirchmunk 0.0.7**, with **gpt-5.4** as the configured search and primary judging model.

## Original documents

The [raw corpus](poc_docs/S/) consists mainly of public US pension-fund RFPs, supplemented by investment due-diligence questionnaires and ESG materials from organizations such as ILPA, INREV, PRI, and AC Private Markets. RFPs describe the services sought, eligibility requirements, proposal deadlines, submission instructions, and contract terms. DDQ materials contain questions about a manager's organization, strategy, investment process, risk controls, operations, and ESG practices; they include templates and supporting materials rather than a uniform set of completed manager responses.

The [download manifest](poc/corpus/manifest_S.csv) records **81 successful downloads**.

| Corpus statistic | Value |
|---|---|
| Original files | 81, with 81 distinct SHA-256 hashes |
| File formats | 78 PDF, 2 DOCX, 1 legacy DOC |
| Total size | 47,379,550 bytes (45.18 MiB) |
| PDF text availability | All 78 have extractable text; no scanned-only PDFs |

The following groups combine the manifest's category labels; every downloaded file is counted once.

| Document group | Files |
|---|---:|
| General and specialist investment-consultant RFPs | 34 |
| Investment-manager and outsourced chief investment officer (OCIO) RFPs | 10 |
| Actuarial and audit RFPs | 12 |
| Custody, deferred-compensation, and pension/retirement-plan service RFPs | 10 |
| RFP questions and answers, and investment-manager questionnaires | 4 |
| DDQ-related documents (manifest category `ddq_template`) | 8 |
| ESG assessment framework and FAQs | 3 |
| **Total** | **81** |

The `ddq_template` category also includes the PRI covering note and NJEDA investment-opportunity notice, so its eight files should not be interpreted as eight standalone DDQ templates. Source URLs, individual categories, download status, sizes, and hashes remain available in the manifest.

Similar documents are intentional: 23 files share the `investment_consultant_rfp` category, and the corpus includes different years or versions of Hawaii ERS RFPs, ILPA DDQs, INREV DDQs, and ILPA ESG FAQs. These provide cases where similar wording can refer to different institutions, versions, or facts. The original PDF/DOCX/DOC files are the search input; extracted text is retained separately for audit and parsing checks. See [methodology](docs/METHODOLOGY.md).

## Evaluation questions

The questions test concrete facts such as deadlines, copy counts, asset thresholds, contract terms, and DDQ section counts, as well as longer summaries, document comparisons, and appropriate refusal when evidence is missing.

The [verified question set](poc/questions/questions_verified.csv) contains **120 unique IDs and 120 distinct question texts**. The exact [frozen campaign input](poc/results/20261014_ABC_verified120/inputs/questions.csv) was used for A, B, and C in the same order. Thus, the campaign has **120 questions and 360 evaluated responses**.

| Question type | Count | Purpose |
|---|---:|---|
| `detail` | 50 | Retrieve a specific fact or short set of requirements |
| `pair_a` | 15 | First question of a similar-wording pair |
| `pair_b` | 15 | Follow-up with a different required answer; detect inappropriate reuse |
| `medium` | 18 | Summarize or combine multiple requirements within a document |
| `broad` | 13 | Compare or synthesize evidence across documents |
| `unanswerable` | 9 | Refuse unsupported or false-premise requests |
| **Total** | **120** | **111 answerable and 9 negative questions** |

The 30 paired questions form **15 pairs**, already included in the 120-question total. Each pair-A immediately precedes its pair-B. By reference-file scope, **98 questions cite one file, 13 cite between four and ten files, and nine negative questions have no gold-source file**. All 81 corpus files appear in at least one question's `gold_source_file`; this is document coverage, not exhaustive coverage of every fact. A document can support multiple questions, and a question can span multiple documents.

Each record includes the question, type, optional pair ID, reference answer (`gold_answer`), source filenames, supporting passage, and verification notes/acceptance criteria. The search runner receives only the ID and question text; reference answers are used for grading, not supplied to search.

For independent verification, three AI reviewers each blind-answered a different batch of 40 questions before seeing the original references. Source comparison and adjudication supported **109 original references** and corrected **11**; six questions also had their scope clarified. All 120 were retained. Each question had one blind reviewer, not three, and this is AI verification rather than human certification. The [verification report](poc/questions/verification/verification_report.md) documents the corrections and limitations; `verify_answer` preserves the initial blind answer and must not replace the adjudicated `gold_answer`.

## 1. Answer accuracy

| Run | Evidence-file limit (`top_k`) | Cluster reuse | Fully correct, including correct refusals | Accuracy | Median search time | Search tokens |
|---|---:|---|---:|---:|---:|---:|
| A | 10 | Off | 74 / 120 | 61.67% | 38.75 s | 11,117,348 |
| B | 5 | Off | 68 / 120 | 56.67% | 39.68 s | 6,194,941 |
| C | 10 | On, similarity threshold 0.85 | 75 / 120 | 62.50% | 41.45 s | 9,267,393 |

All 120 questions remain in each denominator. Partial answers do not count as fully correct. There were 111 answerable questions and nine deliberately unanswerable/false-premise questions. All nine negative questions received an accepted refusal in each run.

Reducing `top_k` from 10 to 5 reduced search tokens by **44.28%**, while six fewer answers were fully correct. It did not reduce the observed median latency. On 50 detail questions, A/B/C answered **40/34/40** correctly. On 13 cross-document synthesis questions, **none was fully correct** in any run; some answers were partially correct.

These are observed results from one pass per configuration, not statistically significant estimates or a production acceptance certificate. The dataset includes intentionally difficult comparisons and is not a random sample of business traffic.

## 2. Similar questions and answer rigor

**C did not start with A's or B's knowledge clusters.** Each run started with an empty, separate cluster store. C asked each of the 120 distinct questions once, in the same order as A and B, and could reuse only clusters created by earlier questions within C. A and C have the same `top_k`; B is the smaller-file-count comparison.

The question set contains **15 adjacent pairs** whose wording is similar but whose answers differ. It contains **no exactly repeated question within C**. This tests inappropriate reuse across different questions, not the benefit of asking an identical question twice.

- C reused an earlier cluster for **9 / 120 questions (7.5%)**.
- **0 / 9 reused answers were correct.** Each reuse case was individually reviewed.
- Seven hits were the second question of a preselected pair; two occurred outside those pairs.
- The same nine questions in A produced four correct answers, four no-results, and one wrong answer.
- Reuse hits averaged **1.72 seconds and 201 tokens**. They were fast but did not answer the new question correctly.

| Earlier question | Later question | Reused answer | Required answer |
|---|---|---|---|
| Number of ILPA v1.2 appendices | Number of ILPA 2.0 appendices | 5 | 8 |
| Boston printed proposal copies | SFERS printed proposal copies | 7 | 3 |
| 2021 ESG FAQ resources | 2024 ESG FAQ resources | 6 | 8 |
| KCERA audit contract term | KCERA actuarial audit scope | One-year contract | Experience-study review, independent valuation, and related audit work |

C's overall score was one answer higher than A's, but that does **not** show that reuse improved accuracy. The other 111 questions gained a net five correct answers, offsetting four lost correct answers in the reuse-hit group. Sampling and model variation remain possible explanations for differences on newly searched questions. See the [matched-question comparison](reports/verified120/reuse_matched_comparison.csv) and [all nine reuse cases](reports/verified120/reuse_cases.csv).

Several wrong-version matches had logged similarities above 0.99. Raising the similarity threshold alone would therefore not resolve every observed error. The KCERA example also shows why matching the document alone is insufficient: the requested fact changed within the same document.

## Read the evidence

- [Full English test report](reports/verified120/report.md): configuration, accuracy, latency, token usage, question types, reuse cases, and limitations.
- [English execution process](poc/results/20261014_ABC_verified120/test_process.md): preparation, commands, timing, failures, repairs, and completion.
- [Question-by-question A/B/C comparison](reports/verified120/question_comparison.csv).
- [All 360 results](reports/verified120/all_results.csv) and [review queue](reports/verified120/review_queue.csv).
- [Question verification report](poc/questions/verification/verification_report.md): 109 supported original answers and 11 corrections, with independent blind-answer records.
- [Evaluation workflow and grading](docs/EVALUATION.md): from submitting a question to retrieval, cluster reuse, answers, acceptance criteria, and final accuracy.
- [Parsing and test methodology](docs/METHODOLOGY.md), [reproduction instructions](docs/REPRODUCING.md), and [artifact guide](docs/ARTIFACTS.md).
- [Data-integrity check](poc/results/20261014_ABC_verified120/validation.json): 360 records, unchanged raw-document hashes, isolated cluster paths, and preserved answers/usage.

## Repository contents

```text
poc_docs/S/                   81 original PDF/DOCX/DOC files
poc/corpus/                   Public source URLs, download manifest, extraction evidence
poc/questions/                Drafts, corrected 120-question set, independent audit
poc/harness/                  Container-side AgenticSearch runner
poc/*.py                      Evaluation, judging, review, export, and validation scripts
poc/results/                  The 120-question A/B/C campaign, raw outputs, logs, and export ZIP
reports/verified120/          English presentation tables and the principal test report
docs/                         English methodology, reproduction, and artifact guides
tools/                        English publication and repository-integrity utilities
provenance/                   Retained-source inventory and publication checks
```

The repository contains one evaluation campaign: `20261014_ABC_verified120`. Question drafts and pre-adjudication snapshots are retained because they form the audit trail for the final 120-question set. The [campaign ZIP](poc/results/20261014_ABC_verified120_export.zip) packages all 473 campaign files with the current English narrative reports; the corpus and full question audit are available separately in this repository.

## Language and evidence policy

The README, current narrative reports, process guide, and presentation tables are in English. Original documents, model outputs, logs, frozen scripts, and audit records remain unchanged for traceability. Some library status messages and malformed legacy-DOC extraction bytes are not English. One actual model answer, **C / INV-04**, was written in Chinese; the English presentation tables provide a clearly recorded translation, without changing its grade. Original answers remain available in `poc/results/`.

All narrative documentation, including the reports inside the campaign ZIP, is in English. Chinese-language report copies have been removed. Original raw evidence may contain multilingual model/library output; English presentation tables provide readable translations without changing the original evidence or grades. See [publication integrity](provenance/README.md) for the preservation and translation rules.

## Verify without calling a model

From the repository root, with Python available:

```bash
python tools/verify_publication.py
```

This checks the copied corpus and evidence, English presentation values, question coverage, and publication inventory. It makes no network or model requests. Follow [REPRODUCING.md](docs/REPRODUCING.md) for a fresh Docker-based experiment; fresh model evaluations consume API tokens.

The next recommended experiment is to keep A as the comparison baseline, add checks for institution/version/mandate/requested fact before reusing a cluster, and improve cross-document coverage. No such algorithm changes or additional search runs were made while packaging this repository.

Third-party documents retain their original rights and attribution. See [DATA_NOTICE.md](DATA_NOTICE.md).
