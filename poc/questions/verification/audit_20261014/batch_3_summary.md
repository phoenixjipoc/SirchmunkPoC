# Independent blind verification — batch 3

Completed all 40 assigned records. Stage A saved every five answers, then completed the legacy DOC corpus checks before any frozen golds were opened. Stage B compared all 40 against the UTF-8 BOM frozen CSV and revisited discrepancies. No other verifier output, source-question edit, Sirchmunk call, paid API or evaluation experiment was used.

Counts: 36 verified; 3 needs correction; 1 ambiguous; 0 unverifiable.

Disputed IDs:

- **SVC-24 — needs_correction:** Clark County’s supplementary 30-day termination statement omits the condition that performance is unsatisfactory in the County’s judgment. Initial terms and renewal options for all four sources are correct. Termination is optional answer context.
- **CONS-15 — needs_correction:** Gold adds “or” before monthly/as-needed phone meetings, suggesting those can replace quarterly in-person meetings. The original lists quarterly in-person meetings plus phone contact.
- **OTH-18 — needs_correction:** Corpus-wide question has only five sources in gold. Add KCERA actuarial audit (one year), St. Louis PRS actuarial auditor (one-time plus unspecified renewal option), and AVFPD OPEB (specified service years, no explicit initial term; optional extensions of unspecified length), or explicitly narrow the question to the five named RFPs.
- **XD-03 — ambiguous:** There are 31 appendix bullets, but one groups TPG & Y Analytics. Ask for participant entries, counting that joint entry once, rather than asserting a count of distinct organisations. CalPERS/CalSTRS representatives are correct.

Important reconciliations:

- **XD-15:** Gold’s six ISO 27001 documents are correct. Blind regex initially missed INREV 2022 “(ISO) 27001” and SC RSIC “ISO/IEC 27001”; bare-number search and source checks resolved both. Blind answer is intentionally retained unchanged; comparison evidence includes all six.
- **INV-24:** Additional gold context for Marquette, Pantheon and NEPC was checked in originals. Arizona’s NEPC contract not being up for bid does not establish a ban on NEPC bidding for the distinct CIO/team assignment. Acceptance notes distinguish scope/context.
- **DDQ-08:** Six resources confirmed. The older FAQ has no printed year, but original PDF CreationDate/ModDate are July 26, 2021; no URL-date inference used.
- **XD-21, XD-24, DDQ-14:** Absence answers verified with explanations distinguishing unreported comment/adoption counts from the blank TMRS fee template.
- **DDQ-11:** Recurring-theme synthesis is supported; do not require an identical taxonomy or assert ESG/IT coverage in every questionnaire.

Coverage: 78 original-derived PDFs, two DOCX and one freshly decoded legacy DOC. PDF evidence uses 1-based physical pages; DOC/DOCX evidence uses section identifiers. Original AC private-markets page 2 and PRI appendix page 2 were rendered/visually checked. Proposed replacement passage fragments were checked in existing `poc/corpus/text_S`.

Deliverables: `blind_answers_3.jsonl` (40 rows), `compare_3.jsonl` (40 rows), `batch_3_summary.md`. Own helpers/previews have the `blind3_` prefix.

Final blind-answer SHA-256 (unchanged during comparison): `94302d679d4d093dc6d97ee3ec7b11a43ed173897e0d71de6e41e5641224606e`.
