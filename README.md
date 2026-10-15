# Sirchmunk PoC

This repository tests two questions:

1. How accurately does Sirchmunk answer questions from raw RFP/DDQ documents?
2. Can similar questions with different answers trigger incorrect cluster reuse?

**81 documents, 120 verified questions, three DEEP runs, 360 responses.** Sirchmunk version: 0.0.7.

## Original documents

The [corpus](poc_docs/S/) mainly contains public pension-fund RFPs and industry DDQ/ESG materials. RFPs specify services, qualifications, deadlines, and contract terms. DDQ materials cover organization, strategy, risk, operations, and ESG; they include templates and supporting notes.

The [manifest](poc/corpus/manifest_S.csv) records 81 successful downloads, with source URLs, categories, sizes, and hashes.

| Corpus statistic | Value |
|---|---|
| Original files | 81, with 81 distinct SHA-256 hashes |
| File formats | 78 PDF, 2 DOCX, 1 legacy DOC |
| Total size | 47,379,550 bytes (45.18 MiB) |
| PDF text availability | All 78 have extractable text; no scanned-only PDFs |

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

Each file is counted once. The eight DDQ-related files include a PRI covering note and NJEDA notice. Similar issuers, years, and versions are intentional; 23 files share the investment-consultant category. Original files remain the search input.

## Questions

The [verified set](poc/questions/questions_verified.csv) has 120 unique questions. A/B/C use the same [frozen input](poc/results/20261014_ABC_verified120/inputs/questions.csv) and order.

| Question type | Count | Purpose |
|---|---:|---|
| `detail` | 50 | Retrieve a specific fact or short set of requirements |
| `pair_a` | 15 | First question of a similar-wording pair |
| `pair_b` | 15 | Follow-up with a different required answer; detect inappropriate reuse |
| `medium` | 18 | Summarize or combine multiple requirements within a document |
| `broad` | 13 | Compare or synthesize evidence across documents |
| `unanswerable` | 9 | Refuse unsupported or false-premise requests |
| **Total** | **120** | **111 answerable and 9 negative questions** |

The 30 paired questions form 15 adjacent pairs, included in the total. There are 98 single-file questions, 13 questions covering four to ten files, and nine negative questions without a gold-source file. References cover all 81 documents, but not every fact in them.

Each record contains the reference answer, sources, passages, and acceptance criteria. Search receives only IDs and questions. Three separate automated review sessions checked 40 questions each before comparing references: 109 were supported and 11 corrected, including six scope clarifications. See the [verification report](poc/questions/verification/verification_report.md).

## 1. Answer accuracy

| Run | Evidence-file limit (`top_k`) | Cluster reuse | Fully correct, including correct refusals | Accuracy | Median search time | Search tokens |
|---|---:|---|---:|---:|---:|---:|
| A | 10 | Off | 74 / 120 | 61.67% | 38.75 s | 11,117,348 |
| B | 5 | Off | 68 / 120 | 56.67% | 39.68 s | 6,194,941 |
| C | 10 | On, similarity threshold 0.85 | 75 / 120 | 62.50% | 41.45 s | 9,267,393 |

**Accuracy = (correct + correct_refusal) / 120.** Partial and unsuccessful answers stay in the denominator. All nine negative questions received accepted refusals in each run. Scoring is automated; see [grading rules](docs/EVALUATION.md).

B used 44.28% fewer search tokens than A, with six fewer correct answers and no median speed improvement. Detail-question scores were 40/34/40 out of 50. No cross-document question was fully correct in any run (13 questions).

These are one-pass results on a deliberately challenging dataset.

## 2. Similar-question rigor

Each run starts with an empty cluster store. C can reuse only earlier C clusters; it does not use A/B clusters or repeat identical questions.

- C reused nine clusters; **all nine answers were wrong**.
- Seven hits were second questions in predefined pairs; two were outside them.
- A answered the same nine questions with four correct, four no-results, and one wrong.
- Reuse hits averaged 1.72 seconds and 201 tokens.

| Earlier question | Later question | Reused answer | Required answer |
|---|---|---|---|
| Number of ILPA v1.2 appendices | Number of ILPA 2.0 appendices | 5 | 8 |
| Boston printed proposal copies | SFERS printed proposal copies | 7 | 3 |
| 2021 ESG FAQ resources | 2024 ESG FAQ resources | 6 | 8 |
| KCERA audit contract term | KCERA actuarial audit scope | One-year contract | Experience-study review, independent valuation, and related audit work |

C's net gain of one correct answer does not establish a reuse benefit: the other 111 questions gained five, offsetting four lost correct answers in reuse cases. Several wrong-version matches exceeded 0.99 similarity, so a higher threshold alone would not fix every case.

See [all reuse cases](reports/verified120/reuse_cases.csv) and the [matched comparison](reports/verified120/reuse_matched_comparison.csv).

## Documentation and results

- [Full report](reports/verified120/report.md), [execution record](poc/results/20261014_ABC_verified120/test_process.md), and [validation](poc/results/20261014_ABC_verified120/validation.json).
- [All 360 answers](reports/verified120/all_results.csv), [A/B/C comparison](reports/verified120/question_comparison.csv), and [190 required reviews](reports/verified120/review_queue.csv).
- [Workflow and grading](docs/EVALUATION.md), [methodology](docs/METHODOLOGY.md), [reproduction](docs/REPRODUCING.md), and [artifact guide](docs/ARTIFACTS.md).

| Directory | Contents |
|---|---|
| `poc_docs/S/` | 81 original files |
| `poc/corpus/` | Sources, download records, and extracted text |
| `poc/questions/` | 120-question set, drafts, and source audit |
| `poc/harness/`, `poc/*.py` | Evaluation, grading, review, and export scripts |
| `poc/results/` | A/B/C answers, logs, clusters, and frozen inputs |
| `reports/verified120/` | English result tables and report |
| `docs/` | Workflow, methodology, reproduction, and file guide |

The corpus and full question audit are separate repository directories. Drafts are retained for rebuilding the verified set.

## Offline validation

All narrative documents are English. Raw evidence retains its original bytes; English presentation tables label translations, including C/INV-04.

```bash
python poc/validate_campaign.py poc/results/20261014_ABC_verified120
```

This checks source hashes, frozen inputs, answer records, scores, and review completion without making service requests.
