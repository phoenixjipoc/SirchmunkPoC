# Evaluation question set

Independent AI verification of 120 questions was completed on October 14, 2026:
109 original references were supported and 11 were corrected against the sources.
Three reviewers each blind-answered a different batch of 40 questions, then
compared their saved answers with the references. This is not human certification.

- `questions.csv`: current master table.
- `questions_verified.csv`: the 120-question evaluation-ready snapshot.
- [Verification report](verification/verification_report.md): methods, corrections,
  limitations, and effects on earlier experiments.
- `verification/audit_20261014/`: original versions, frozen blind answers,
  per-question evidence, and adjudications.
- `draft_*.jsonl`: unchanged drafting inputs. Approved corrections in
  `verification/approved_corrections.jsonl` override specified fields on rebuild.

`gold_answer` is the adjudicated reference. `verify_answer` preserves the initial
blind answer, including mistakes found later. `verify_status` is `verified` or
`corrected`; `verify_note` records differences and acceptance criteria.
`review_status` remains `auto_drafted`, preserving its meaning in the original
human-review workflow. AI verification is not marked as human approval.

Rebuild: `python poc/questions/build_questions.py`.
Republish the audit snapshot:
`python poc/questions/verification/finalize_verification.py`.
Do not overwrite this audit's `verification/blind_*.jsonl`; use separate inputs
for a new blind review.

The six drafts and the original 120-row snapshot are retained as inputs to this
verification process. Reference verification is separate from measuring
search-answer quality. The full 120-question A/B/C experiment is described in
the repository's main README and English report.
