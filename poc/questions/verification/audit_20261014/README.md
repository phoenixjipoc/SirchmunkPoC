# Independent verification of the 120-question set

Audit date: 2026-10-14 (Asia/Shanghai).

Completed: 120/120 independently reviewed; 109 verified and 11 corrected after
source adjudication. All 120 are included in `../../questions_verified.csv`.
See `../verification_report.md` for the English report and correction list.

## Method

Three fresh AI reviewers receive disjoint sets of 40 questions. They see only
question IDs, question text, and the 81-document corpus during the blind phase.
They must save all 40 independent answers before opening the frozen gold answers.
They then compare each answer semantically against the gold, revisiting sources
for disagreements. The coordinating reviewer adjudicates disputes separately.
This is independent AI review; it is not business-user or human certification.

The original questions and drafts are preserved in `original/`; hashes are in
`input_hashes.json`. Original document hashes and extraction methods are recorded
in `source_inventory.json`. PDF page numbers mean 1-based physical PDF pages.
DOCX references use section names. The legacy DOC extractor does not render pages.

## Files

- `source_text/`: new text extraction from original PDFs/DOCX; original legacy
  DOC text recovered from its Word binary text piece table. Used only for review.
- `blind_answers_1.jsonl` through `blind_answers_3.jsonl`: independent answers,
  source locators, quotations, confidence, and search notes. Saved progressively.
- `compare_1.jsonl` through `compare_3.jsonl`: comparison to the original golds,
  proposed corrections, ambiguity findings, and acceptable answer variants.
- `mechanical_checks.json`: ID coverage, quote matching, and PDF page-locator checks.
  Matching a quote proves provenance, not semantic correctness or completeness.
- `adjudications.jsonl`: coordinating review of disagreements. Suggested edits
  are applied only if explicitly accepted here.
- `completion.json`: written only after all 120 blind answers/comparisons exist,
  source checks pass, and all disputes have a disposition.
- `publication_checks.json`: raw-document, frozen-input and draft integrity;
  approved-change-only check; IDs affecting the historical 48-question run.
- `blind_frozen/` and `blind_answer_hashes.json`: frozen initial independent
  answers, including any mistakes discovered during subsequent comparison.

Final statuses: `verified` (gold supported), `corrected` (adjudicated correction),
`needs_human_review` (unresolved scope/ambiguity), `unverifiable` (source insufficient).
Only verified/corrected questions belong in the evaluation-ready subset.
`review_status` is reserved for the existing human review workflow and is not
changed to human-verified by this audit.

## Rebuilding

`python poc/questions/verification/check_verification.py --complete` checks coverage
and source quotes. `finalize_verification.py` publishes comparisons and accepted
corrections, rebuilds `questions.csv`, and writes `questions_verified.csv`.
`build_questions.py` applies `verification/approved_corrections.jsonl` over the
preserved draft data, so approved changes survive rebuilding. It fails without
overwriting the master dataset when validation fails.

The old 48-question experiment outputs remain historical. If a gold answer changes,
old correctness labels may be stale; this audit does not regrade or rerun Sirchmunk.
No claim of 100% answer accuracy follows from independent AI agreement.
