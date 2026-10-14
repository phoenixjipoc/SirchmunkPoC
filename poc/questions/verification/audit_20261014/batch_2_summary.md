# Independent verification batch 2

Completed exactly the 40 IDs in `blind_2.jsonl`. All 40 blind answers were saved, in five-question batches, before opening the frozen gold CSV. No other verifier's answers were read; no agents, external APIs, Sirchmunk calls or evaluation experiments were used.

| Result | Count |
|---|---:|
| Blind answers | 40 |
| Comparison rows | 40 |
| Verified | 36 |
| Needs correction | 4 |
| Ambiguous | 0 |
| Unverifiable | 0 |

Disputed gold IDs:

- **INV-23:** Baltimore BCERS does state a five-year contract and requests agreement/fees for two two-year options (physical pp24, 27). Replace the gold's “no contract term” statement and add its source. The proposed question names the specialist RFPs to bound corpus coverage. Missouri's p7 explicitly supports one year plus an additional two years; the gold is correct on that point.
- **XD-17:** LAFPP's generic appendix contains PSC-36's Iran affidavit clause, but Section 1.22 explicitly exempts PSC-36 (physical p25, visually verified). Distinguish three applicable Iran requirements from LAFPP's included but exempt clause; do not describe four operative requirements.
- **CONS-14:** The gold lists only six of ten Section 2 minimum-requirement bullets. Add conflicts, Appendix E contract acceptance, SEC registration, all five insurance limits, and Appendix A certification. Section 2 and Appendix A differ on client-threshold/history language and dates; the proposed question explicitly scopes the answer to Section 2 rather than silently reconciling them.
- **DDQ-10:** Section 19 has **seven**, not six, subsections. Add 19.7 Additional Information, including other ESG practices and the management company's internal ESG risks/opportunities (physical p42).

**DDQ-04** remains verified; a stronger verbatim gold passage is proposed because the existing table fragment omits “every 2-3 years.” This is evidence improvement, not an answer correction.

Source rechecks also corrected blind-stage limitations, retained transparently in comparison notes: XD-14 has eight questions (the blind answer stopped at 10.6); INV-23's Missouri extension is explicitly additional and Arizona's 3+1+1 term is in scope; XD-17's LAFPP exemption overrides the initial blind reading. The saved blind answers were not rewritten after comparison began.

The three negative-answer cases are supported within the supplied corpus: XD-20 has a false pass-score premise, XD-23 lacks the specified LACERA RFP, and DDQ-13 is an unfilled applicant questionnaire rather than an award announcement. Searches included all 81 fresh original-source extractions, including the recovered legacy DOC. These findings make no claims about outside documents.

Validation: 40 unique comparison IDs in the required order; all 121 blind quotes and all 134 comparison evidence quotes match fresh or existing corpus text after whitespace normalization; no detected physical-page mismatch; every proposed gold-passage fragment matches existing `poc/corpus/text_S` text. Shrewsbury's scrambled fresh extraction was checked against the original page image and readable existing extraction. Output is valid UTF-8 JSONL. Optional gold elaborations are explicitly not mandatory in acceptance notes.

Blind file SHA-256, unchanged during comparison: `45a2580fffe0331ee82f5de09d647c0a4d4161752ea1e7130db4a953c10e7cff`.

Deliverables: `blind_answers_2.jsonl`, `compare_2.jsonl`, and this summary. Agent-owned supporting files use the `agent2_` prefix. No source questions, shared scripts, or other agents' outputs were changed.
