# Retrieval questions and source references

This dataset supplies the 120 retrieval queries and their expected supporting sources. Reference answers describe the facts a retrieved document must contain; they are not generated-answer results. Search receives only the question fields. Source criteria stay in the separate assessment inputs.

The 120-question reference audit supported 109 original answers and corrected 11. Three separate automated review sessions blind-answered 40 questions each before comparing references.

| File | Purpose |
|---|---|
| `questions.csv` | Current master |
| `questions_verified.csv` | Frozen source for the retrieval inputs |
| `verification/verification_report.md` | Method, corrections, and limits |
| `verification/audit_20261014/` | Frozen inputs, blind answers, evidence, and decisions |
| `draft_*.jsonl` | Six drafts used to build the 120-question set |
| `verification/approved_corrections.jsonl` | Changes applied during rebuild |

Use `gold_answer` as the final reference. `verify_answer` preserves the initial blind answer, including later-discovered mistakes. Acceptance criteria follow `Acceptance:` in `verify_note`. The workflow field `review_status` remains `auto_drafted`; verification is recorded separately.

Rebuild with `python poc/questions/build_questions.py`. Republish a complete audit with `python poc/questions/verification/finalize_verification.py`. Preserve the recorded blind inputs when starting a new audit.
