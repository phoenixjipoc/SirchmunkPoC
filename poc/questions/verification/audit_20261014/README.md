# Question audit

Completed October 14, 2026: 120 references reviewed, 109 supported, 11 corrected. All remain in `../../questions_verified.csv`; see `../verification_report.md` for decisions.

Three separate automated review sessions answered 40 questions each using only questions and sources. Answers were saved before comparison with references. Disagreements received source adjudication.

| Files | Contents |
|---|---|
| `original/`, `input_hashes.json` | Initial 120-row question set and six drafts |
| `source_inventory.json`, `source_text/` | Document hashes and separate audit extraction |
| `blind_answers_*.jsonl` | Blind answers, locators, and quotations |
| `blind_frozen/`, `blind_answer_hashes.json` | Preserved initial answers and hashes |
| `compare_*.jsonl` | Reference comparisons and acceptance criteria |
| `adjudications.jsonl` | Final disagreement decisions |
| `mechanical_checks.json` | Coverage, quotation, and page checks |
| `publication_checks.json`, `completion.json` | Integrity and completion records |

PDF locators use physical pages; DOC/DOCX references use sections. Audit extraction is separate from search input. Quote matching checks provenance, not complete interpretation.

`python poc/questions/verification/check_verification.py --complete` checks coverage and quotations. `finalize_verification.py` publishes accepted changes, and `build_questions.py` applies them over preserved drafts. Only `verified` and `corrected` references are evaluation-ready; the review-status field is unchanged.
