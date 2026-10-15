# Independent verification of 120 questions

Completed October 14, 2026, against 81 original documents. This reference audit
did not itself run a Sirchmunk evaluation; the subsequent A/B/C experiment is
reported separately.

## Outcome

| Item | Count |
|---|---:|
| Independent blind answers and comparisons completed | 120 |
| Original questions/references supported (`verified`) | 109 |
| Corrected after source adjudication (`corrected`) | 11 |
| Questions whose scope was also clarified | 6 |
| Unresolved questions requiring exclusion | 0 |
| Questions available for evaluation | 120 |

Seven references were incorrect/incomplete and four had scope/interpretation
problems. All eleven received approved corrections. Audit completion does not
mean 100% reference accuracy and is not a Sirchmunk accuracy result.

## Method

1. Freeze the original question set and six draft batches; hash the documents.
2. Run three separate automated review sessions on disjoint batches of 40. During blind
   answering, provide only questions and documents. Each reviewer saves all 40
   answers before seeing the original references. Each question has one blind
   reviewer, not three repeated blind reviews.
3. Compare answers semantically, recording original passages, physical PDF pages
   or sections, disagreements, and acceptance criteria. The coordinating reviewer
   revisits the source to adjudicate all eleven disputed questions.
4. Preserve original blind answers, including mistakes discovered later. Both the
   original reference and initial blind answer missed LAFPP's controlling exemption;
   subsequent source adjudication found it.
5. Check ID coverage, duplicates, source files, quotation/page provenance, and
   application of only approved changes to the published reference set.

## Eleven corrections

| ID | Problem found | Approved correction |
|---|---|---|
| INV-22 | Specialist consulting scope and firm/key-person experience unclear; TRS permits comparable experience | Name six RFPs, describe requirements and alternatives per file, remove misleading uniform experience range |
| INV-23 | Baltimore five-year term and two two-year options omitted; comparison scope unclear | Name ten files, add Baltimore, use Missouri's explicit one-year-plus-two-year provision |
| SVC-10 | OCERS minimum insurance list conflicts with sample-contract words/numerals | Narrow to the minimum-qualification insurance list; retain sample inconsistency note |
| SVC-24 | Clark early termination described as unconditional | Include the county's unsatisfactory-performance condition and 30-day notice |
| CONS-14 | Hartford list omitted four of ten requirements; main text and appendix differ | Limit to Section 2; include all ten requirements, five insurance limits, deadline and certifications |
| CONS-15 | Creve Coeur quarterly on-site meetings and monthly/as-needed calls presented as alternatives | Require quarterly on-site meetings plus monthly or as-needed calls |
| CONS-16 | Denominator for modal experience requirement undefined | Name ten general-consulting RFPs; mode five years: four five-year, three ten-year, two seven-year, one three-year; retain COAERS alternative |
| DDQ-10 | ILPA ESG section described as six subsections | Correct to seven, adding 19.7 Additional Information and management-company ESG |
| OTH-18 | Actuarial contract comparison omitted three solicitations | Add KCERA, St. Louis PRS and AVFPD; distinguish contract term, one-time work, and service years |
| XD-03 | Counting convention for a jointly named contributor unclear | Count 31 entries; TPG & Y Analytics is one entry |
| XD-17 | LAFPP generic Iran clause treated as operative | Main text exempts PSC-36; retain three operative requirements plus the LAFPP exemption |

## Files and fields

- `../questions.csv`: updated 120-question master.
- `../questions_verified.csv`: evaluation-ready snapshot, identical at audit publication.
- `approved_corrections.jsonl`: original values, approved replacements, and reasons.
- `compare_audit_20261014.jsonl`: final conclusions, evidence, and acceptance criteria.
- `audit_20261014/`: original snapshot, blind/comparison batches, adjudications,
  source inventory, and check results.

Use `gold_answer` as the adjudicated reference. `verify_answer` remains the initial
blind answer: some entries contain later-discovered mistakes or answer the
original broader question. Interpret it with `verify_status`, `verify_note`, and
the final reference; it is not a replacement gold answer. The workflow field
`review_status` remains `auto_drafted`; automated verification is recorded in `verify_*`.

## Checks and limits

- 120 complete unique IDs, three batches of 40; frozen blind-answer hashes match.
- 81 raw files, six drafts, and seven frozen inputs were unchanged. Audit text
  was saved separately; original PDFs/DOCX/DOC remained the search corpus.
- 802 citation records passed provenance checks: 387 blind-answer and 415
  comparison references. These include duplicate citations and one explicitly
  identified PDF-metadata reference. Numeric physical PDF page references were
  checked; DOC/DOCX references use sections.
- Quote matching establishes provenance, not completeness or correct interpretation.
  Semantic conclusions come from independent comparison and source adjudication.
- The original 120-question snapshot and six draft batches are retained so that
  approved corrections can be traced and the final dataset can be rebuilt.

The later October 14 DEEP campaign used this corrected snapshot and its acceptance
criteria. Automated agreement remains subject to error.
