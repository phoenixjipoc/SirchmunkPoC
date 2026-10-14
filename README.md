# Sirchmunk PoC: answer accuracy and similar-question robustness

This repository contains the public document corpus, evaluation questions, verification records, harness, execution history, and results for a Sirchmunk proof of concept. It investigates two questions:

1. **How accurately does Sirchmunk answer questions from raw RFP and DDQ documents?**
2. **When questions look similar but require different answers, does knowledge-cluster reuse preserve the correct institution, document version, and requested fact, or mistakenly reuse an unsuitable answer?**

The principal experiment was completed on **October 14, 2026**: **81 original documents, 120 source-verified questions, and three sequential DEEP runs (360 evaluations)**. The tested library was **Sirchmunk 0.0.7**, with **gpt-5.4** as the configured search and primary judging model. DDQ means **Due Diligence Questionnaire**; RFP means **Request for Proposal**.

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
- [Parsing and test methodology](docs/METHODOLOGY.md), [reproduction instructions](docs/REPRODUCING.md), and [artifact guide](docs/ARTIFACTS.md).
- [Data-integrity check](poc/results/20261014_ABC_verified120/validation.json): 360 records, unchanged raw-document hashes, isolated cluster paths, and preserved answers/usage.

## Repository contents

```text
poc_docs/S/                   81 original PDF/DOCX/DOC files
poc/corpus/                   Public source URLs, download manifest, extraction evidence
poc/questions/                Drafts, corrected 120-question set, independent audit
poc/harness/                  Container-side AgenticSearch runner
poc/*.py                      Evaluation, judging, review, export, and validation scripts
poc/results/                  All historical runs, raw outputs, logs, and cluster exports
reports/verified120/          English presentation tables and the principal test report
docs/                         English methodology, reproduction, and artifact guides
tools/                        English publication and repository-integrity utilities
provenance/                   Copy inventory, publication checks, original translated prose
HANDOFF_sirchmunk_poc.md       Original early planning handoff; not current run status
```

The October 7 smoke tests and three 48-question runs are retained as historical evidence. Five of those questions were later affected by reference corrections, and token-accounting instrumentation also changed. Their old scores must not be pooled with the October 14 results.

## Language and evidence policy

The README, current narrative reports, process guide, and presentation tables are in English. Original documents, model outputs, logs, frozen scripts, and audit records remain unchanged for traceability. Some library status messages and malformed legacy-DOC extraction bytes are not English. One actual model answer, **C / INV-04**, was written in Chinese; the English presentation tables provide a clearly recorded translation, without changing its grade. Original answers remain available in `poc/results/`.

Original Chinese narrative documents are retained under `provenance/original_documentation/`. The existing ZIP is also the original export, not a newly translated archive. See [publication integrity](provenance/README.md) for exact preservation and translation rules.

## Verify without calling a model

From the repository root, with Python available:

```bash
python tools/verify_publication.py
```

This checks the copied corpus and evidence, English presentation values, question coverage, and publication inventory. It makes no network or model requests. Follow [REPRODUCING.md](docs/REPRODUCING.md) for a fresh Docker-based experiment; fresh model evaluations consume API tokens.

The next recommended experiment is to keep A as the comparison baseline, add checks for institution/version/mandate/requested fact before reusing a cluster, and improve cross-document coverage. No such algorithm changes or additional search runs were made while packaging this repository.

Third-party documents retain their original rights and attribution. See [DATA_NOTICE.md](DATA_NOTICE.md).
