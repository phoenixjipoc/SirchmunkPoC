# Independent verifier 1

Completed exactly the 40 records in `blind_1.jsonl`. Blind answers were appended in eight batches of five and validated before the first read of frozen `original/questions.csv`. Blind answers remain unchanged after comparison. No other verifier results, external APIs, Sirchmunk calls, or evaluation experiments were used.

| Comparison status | Count |
|---|---:|
| verified | 37 |
| needs_correction | 0 |
| ambiguous | 3 |
| unverifiable | 0 |
| Total | 40 |

Disputed IDs:

- **INV-22 — scope and role ambiguity.** Gold's numerical requirements are supported, but the question does not define whether broader alternatives/private-markets mandates belong in the comparison. Gold includes Baltimore and LAGERS; other plausible sources include FPIF and INPRS. SBCERS's ten-year rule applies to at least one key assigned professional, not necessarily the lead. Proposed question explicitly names the six intended sources and distinguishes the SBCERS role. TRS's 20% time commitment is optional context.
- **SVC-10 — internal source inconsistency.** The minimum-qualifications list on physical PDF page 4 clearly gives umbrella $5m/$5m and professional liability $2m/$3m. The sample agreement on page 21 says **“one million dollars ($2,000,000) per occurrence”**. Original page rendered and visually confirmed. Proposed question specifies the minimum-qualifications list; proposed answer preserves its limits and flags the conflicting words.
- **CONS-16 — unstated general-consulting restriction.** Five years remains the modal answer, but the gold's four-five-year versus three-ten-year count applies to general-consulting RFPs, not the full investment-consulting corpus. Proposed question excludes specialist mandates. Rechecked Hartford's ten-year minimum. Hawaii 2022 PE has ten years in main qualifications (p17) but five in certification (p29), correcting the blind-stage unqualified use of its five-year certification as a data point.

Other findings:

- **DDQ-09 and OTH-16:** answers verified; proposed verbatim passage fragments extend incomplete stored evidence to all eight ESG resources and both actuarial experience requirements, respectively.
- **XD-16:** fresh original legacy DOC extraction confirms section 2.3.4 and resolves the blind-stage extraction caveat. Four direct firm-signatory documents verified. SURS's overlaid heading was resolved by viewing original page 32.
- **XD-19:** month remains unavailable. The frozen explanatory note that 2022 appears only in the filename is inaccurate: the DOCX header contains “DDQ 2022.” This still supplies no publication month.
- **XD-22:** questionnaire prompt with no supplied or prescribed position limit; **DDQ-12:** no completed KKR assessment, with explicit ILPA non-scoring language. These are supported abstentions, not failed verification.

Validation passed: 40 unique in-scope IDs in each JSONL, matching question order, preserved blind answers/source fields, complete comparison schema, existing original source files, and every proposed gold-passage fragment found verbatim in existing `poc/corpus/text_S`. Comparison evidence uses physical PDF pages or DOCX/DOC section identifiers. Acceptance notes distinguish required answers from optional gold elaboration.

Deliverables: `blind_answers_1.jsonl`, `compare_1.jsonl`, `batch_1_summary.md`. Only these and verifier-owned `blind1_` helpers/previews were created.
