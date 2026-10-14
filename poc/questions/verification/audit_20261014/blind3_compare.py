from blind3_helper import *
import csv, hashlib
from collections import Counter

bp=AUDIT/'blind_answers_3.jsonl'
before=hashlib.sha256(bp.read_bytes()).hexdigest()
blind=[json.loads(x) for x in bp.read_text(encoding='utf-8').splitlines()]
assert len(blind)==40 and len({x['id'] for x in blind})==40
gold={x['id']:x for x in csv.DictReader((AUDIT/'original/questions.csv').open(encoding='utf-8-sig',newline='')) if x['id'] in {b['id'] for b in blind}}
assert len(gold)==40

notes={
'INV-03':('Gold matches the independent answer and Attachment 3 question 2: up to ten, each greater than $1bn.','Accept up to ten / no more than ten and >$1bn. Contact-detail fields and similar-work context are supplementary; exactly ten or at least $1bn is not equivalent.'),
'INV-06':('All four investment/commitment amounts and the as-of date agree.','Accept approximately $164m/$59m/$25m/$88m mapped to the four requested categories. Issuer, solicitation number and total $4.2bn fund size are optional.'),
'INV-09':('Core requirements agree. Reviewed the original SURS cover/timetable and qualification clauses; five-year live history has a template as-of-year placeholder, and the ownership exemption applies.','Accept five-year live strategy record and the alternative client tests (two >$1bn U.S. public pensions OR one >$10bn public plan). Ownership exemption is a relevant qualification. Issuer, litigation criterion and placeholder date need not be volunteered.'),
'INV-12':('Independent answer matches the four manager-selection factors; this is not the three-factor consultant RFP.','Accept People, Process, Performance, Pricing and faithful descriptions; exact labels are not mandatory.'),
'INV-15':('Seven years matches the firm minimum. Also checked the gold’s supplementary November 8, 2024 qualification deadline on physical page 8.','Seven years is sufficient for the narrow question. Service type and qualification deadline are optional; five-year staff experience is not the firm threshold.'),
'INV-18':('All nine timetable milestones match the complete source table.','Accept equivalent date formatting and March 13–17 as a range. The amendment reservation is optional.'),
'INV-21':('All ten criteria match section V, physical pages 12–13.','Accept paraphrasing and grouped descriptions retaining the ten substantive criteria. Ordering and exact wording are not required.'),
'INV-24':('The three specialist incumbents in the blind answer are correct. Stage B source revisits confirm additional gold facts: BCERS Marquette may not bid (p9); DCRB also names Pantheon as PE specialist (p3); Arizona names NEPC and says its Board contract is not up for bid (p2). Gold is supported, but Arizona is a broader general consulting procurement. No inference that NEPC is prohibited from bidding for the separate CIO/team mandate is justified.','Require the specialist incumbents and their stated eligibility. Marquette exclusion is material when discussing BCERS existing consultants. Treat Arizona/NEPC as additional scope context rather than forcing it into a specialist-only interpretation. Pantheon bid eligibility is not stated.'),
'SVC-03':('Fee and lending allocation exactly agree with Q27 and Q18.','Accept $580,000 flat and 80% OCERS / 20% State Street. Service enumeration is optional. Do not insist on annual frequency, which the quoted answer does not expressly state.'),
'SVC-06':('Minimum annual deferral and two-business-day receipt-based investment deadline agree. The original cover confirms August 4, 2023.','Accept $260 per plan year and within two business days after receipt. Issuer, date and Model Plan section numbers are optional.'),
'SVC-09':('Gold matches custody minimum qualifications on physical pages 16–17.','Accept $100bn international equity/fixed income and $75m liability/professional E&O coverage. Issuer/date are optional.'),
'SVC-12':('Main-plan and separate OBRA figures agree.','Main plan 4,398 participants / $308,676,730 is sufficient. OBRA 536 / $926,785 is supplementary and must not replace or be silently added to main-plan figures.'),
'SVC-15':('Three years plus up to three additional years by mutual agreement is confirmed. Supplementary audit years are confirmed on physical page 5.','Accept 3+up to3 years, mutual extension. Audit fiscal years and annual-review/negotiation detail need not all be volunteered.'),
'SVC-18':('All nine Attachment 2 minimum qualifications agree with the independent list. Section I.C has general knowledge/authorization guidelines; Attachment 2 desirable criteria are separate.','Accept a faithful summary of the nine requirements. Do not impose desirable two audits of >$3bn plans or a California license for manager/supervisor as minimums; a U.S.-state license suffices for those roles.'),
'SVC-21':('Gold faithfully summarizes all thirteen oversight responsibilities plus on-site delivery and monthly reporting.','Accept grouped duties covering planning/procurement, PAS implementation oversight, deliverables/schedule/budget/vendors, sign-offs, communication/issues/risk/change/quality and reporting. Separate PAS procurement/implementation details beyond the oversight list are optional.'),
'SVC-24':('Initial terms/extensions for all four solicitations match. However the gold adds unqualified Clark County termination on 30 days notice; page 9 makes this conditional on unsatisfactory performance, solely in the County’s judgment. Qualify that optional clause or omit it.','The question asks initial terms and renewal/extension options. Termination rights are optional; a correct answer omitting termination is fully acceptable. Clark’s 5/7/10-year pricing template does not replace its explicit 3+7 period clause.'),
'XD-03':('Source contains exactly 31 appendix bullets, including one joint entry “TPG & Y Analytics.” Both named representatives match. The gold equates bullet entries with organisations without stating how the joint label is counted; the source does not establish a count of distinct legal organisations. Clarify the question to ask listed entries.','Accept 31 listed/grouped participant entries with James Andrus for CalPERS and Nicholas Abel for CalSTRS. A respondent flagging the joint TPG/Y Analytics counting issue should not be failed for not asserting 31 distinct organisations.'),
'XD-06':('Threshold and location agree: ILPA DDQ 2.0 Q7.14, section 7 Credit Facilities.','Accept more than ten business days and Credit Facilities. Question number, document version and illustrative circumstances are helpful but not all mandatory for the narrow threshold/section question.'),
'XD-09':('Five appendices A–E and titles agree with v1.2 contents, distinct from v2.0 A–H.','Accept five with the five titles; punctuation, Templates prefixes and order variations do not change meaning.'),
'XD-12':('All five red flags match original page 2 right column, visually inspected to resolve interleaved extraction.','Accept paraphrases of departures, complaints/regulatory/litigation history, capacity limits, closing to new investors, and biggest strategy risk. Adjacent liquidity questions are not part of this list.'),
'XD-15':('Gold is correct at six. My blind search pattern ISO.?27001 missed “(ISO) 27001” in the INREV 2022 DOCX and “ISO/IEC 27001” in SC RSIC. Stage B searched the bare number 27001 across all 81 original-derived texts and revisited both sources; no seventh match. The saved blind answer remains unchanged to preserve independence.','Accept all six documents with correct policy/compliance/certification/security-program contexts. No requirement that every source mandates certification: ILPA/INREV/SC RSIC are questionnaire prompts, while TRS contains a contractual program requirement.'),
'XD-18':('Four non-ILPA/non-PRI references and purposes agree. Legacy original-derived .doc checked as well; no additional ILPA mention.','Accept the four documents and purposes; template title/transaction classification may be paraphrased.'),
'XD-21':('NOT IN CORPUS is supported: full PRI note states significant written/verbal comments over four months but no numeric count; related ILPA materials and corpus references add no count.','Accept no count disclosed / cannot determine from corpus with narrative explanation. Do not require literal NOT IN CORPUS; 31 participants is not a comment count.'),
'XD-24':('NOT IN CORPUS is supported. Section VIII solicits proposed fees and sample article 3.1 has a blank annual dollar field; neither establishes the incumbent’s actual fee. Other TMRS corpus references and legacy text provide no figure.','Accept not disclosed/unknown from supplied documents; distinguish blank proposed-fee template from actual incumbent remuneration. No guessed dollar amount.'),
'CONS-03':('Gold $2bn matches section 3.A.1. The attached policy’s $500m minimum applies to investment managers, not consultant proposers.','Accept at least $2bn under management.'),
'CONS-06':('TMRS identification and both non-discretionary public-plan client thresholds match.','TMRS or the full system name is sufficient; repeating thresholds is optional.'),
'CONS-09':('TRS Illinois identification matches Appendix B combined-client-assets certification.','TRS Illinois / Teachers’ Retirement System of the State of Illinois is sufficient; FY23 and appendix identifier are optional.'),
'CONS-12':('Seven printed copies matches two source instructions.','Seven printed copies alone answers the question; electronic copy is optional context.'),
'CONS-15':('Eight functions otherwise agree, but gold adds “or” between quarterly in-person meetings and monthly/as-needed phone contact. The source says “quarterly in person, monthly or as needed by phone,” requiring both modes/cadences rather than offering telephone contact as a substitute for quarterly visits. Remove the added alternative.','Accept all eight functions summarized. Quarterly in-person meetings plus monthly/as-needed phone contact is correct; exact punctuation is not required.'),
'DDQ-02':('NJEDA Appendix A question 4.6 matches. The original PDF itself contains the appendix excerpt, physical p3/printed p17.','NJEDA Life Science Seed Fund DDQ is sufficient identification; 2023, Appendix A and Q4.6 are optional supporting detail.'),
'DDQ-05':('Launch and update dates match the 2018 introduction.','Accept April 2007 and 2010/2014/2018. Phased approach and stage labels are not required.'),
'DDQ-08':('All six resources match the older FAQ p3. Its visible text has no printed publication year; Stage B checked the original PDF metadata: CreationDate and ModDate are July 26, 2021. This supports identifying the supplied file as the 2021 version without using a URL date.','Accept six and recognisable names/acronyms. No publication-date proof is required in the answer; do not mix in the two additional 2024 resources.'),
'DDQ-11':('Gold is a defensible synthesis of recurring themes, not a universal all-documents intersection. Independently reviewed the additional INREV 2022 and legacy FoF questionnaires; they support the same core categories. No single canonical taxonomy is stated by the corpus.','Accept materially equivalent grouping of firm/team, strategy/process, fees/terms, performance, reporting/valuation, governance/risk/compliance and operations. ESG/diversity are recurring in relevant subsets, not mandatory claims about every DDQ. Do not require exact eight-item wording or every optional subtopic.'),
'DDQ-14':('NOT IN CORPUS is supported by checking ILPA adoption references, 2024 FAQ, PRI note and all other ILPA references, including newly decoded legacy source. No GP adopter census appears.','Accept no figure disclosed / cannot determine. Neither voluntary adoption language nor 2024 framework revision provides a count.'),
'OTH-03':('Both plan participant counts and as-of date match original page 1.','Accept 8,828 for 401(a) and 7,533 for 403(b); do not transpose.'),
'OTH-06':('Approximate combined $167m and Lincoln Financial match executive summary.','Accept approximately $167m (or appropriately reconciled table total) and Lincoln Financial; not just County-only $162.85m.'),
'OTH-09':('Both mandate cap and firm AUM limit match; gold correctly distinguishes underlying-manager preference.','Accept up to $350m and firm AUM strictly below $30bn. Cook County identification is optional.'),
'OTH-12':('Timetable and submission instructions both confirm September 30, 2022 at 4:30pm HST.','Accept date/time/Hawaii Standard Time equivalents. Issue date, RFP number and later best-and-final deadline are optional context.'),
'OTH-15':('15 years including three with similar California public pension clients matches minimum qualification.','Accept 15 total and three California years. Do not require credential details unrelated to the years asked.'),
'OTH-18':('The five listed terms are correct, but the question asks the actuarial-services RFPs across the corpus and does not exclude actuarial audits or OPEB. Gold omits KCERA actuarial audit (one year), St. Louis PRS actuarial auditor (one-time with renewal option), and AVFPD OPEB (2024–2029 service schedule, optional extensions not dimensioned). Either broaden gold to all eight as proposed or explicitly restrict the question to the five named systems.','Accept alternative order/wording of the eight applicable sources. AVFPD service years are not an expressly fixed contract term; St. Louis one-time is not one year. Annual COAERS engagement letters are not renewal options. If the question is narrowed to five named RFPs, the original five-item answer becomes sufficient.')
}

def passage(key,quote):
    p=OLD/(source(key).name+'.txt')
    t=p.read_text(encoding='utf-8-sig')
    pattern=r'\s+'.join(re.escape(x) for x in norm(quote).split(' '))
    m=re.search(pattern,t)
    if not m: raise ValueError(('Not found in existing text_S',key,quote))
    return m.group(0)

out=[]
for b in blind:
    id=b['id'];g=gold[id]
    assert b['question']==g['question']
    note,accept=notes[id]
    r=dict(id=id,status='verified',blind_answer=b['blind_answer'],blind_source_file=b['blind_source_file'],note=note,evidence=list(b['evidence']),proposed_changes={},acceptance_notes=accept,reviewer='independent_agent_3',verification_method='blind_answer_then_gold_comparison')
    if id=='INV-24':
        r['evidence'] += [ev('Baltimore_BCERS','Marquette will not be permitted to submit a proposal in this search.'),ev('DC_Retirement','Pantheon as a specialist consultant for private equity.'),ev('Arizona_PSPRS','The Board contracts with its own consultant, NEPC, to serve as its fiduciary consultant; the Board’s consultant contract is not up for bid.')]
    if id=='XD-15':
        r['evidence'] += [ev('INREV__INREV-DDQ-2022','Are you compliant with International Organization for Standardization (ISO) 27001 or any other cyber security or information security certifications?','3.3.2'),ev('SC_RSIC','RSIC data (i.e., ISO/IEC 27001, FISMA, FedRAMP, CJIS, etc.)?')]
    if id=='DDQ-08':
        r['evidence'].append({'file':source('ILPA__ESG-Assessment-Framework-FAQ').name,'page':'PDF metadata: CreationDate and ModDate','quote':"D:20210726115517-04'00'"})
    if id=='XD-03':
        r['status']='ambiguous'
        r['proposed_changes']={'question':"How many working-group participant entries are listed in the appendix of the PRI covering note on the 2021 update of its private equity responsible investment DDQ (counting the joint TPG & Y Analytics entry once), and who represented CalPERS and CalSTRS?",'gold_answer':"31 listed participant entries, counting TPG & Y Analytics once. CalPERS was represented by James Andrus; CalSTRS by Nicholas Abel."}
    if id=='SVC-24':
        r['status']='needs_correction'
        q='The county also reserves the right to terminate the contract, with thirty (30) days written notice, at any time if the requirements of the contract are not being met satisfactorily, solely in the county’s judgment.'
        r['evidence'].append(ev('Clark_County',q))
        r['proposed_changes']={'gold_answer':g['gold_answer'].replace('terminable on 30 days\' notice.',"terminable by the County on 30 days’ written notice if, solely in its judgment, contract requirements are not being met satisfactorily."),'gold_passage':g['gold_passage']+' | '+passage('Clark_County',q)}
    if id=='CONS-15':
        r['status']='needs_correction'
        q='Follow recommended investments closely and meet with the Pension Board quarterly in person, monthly or as needed by phone.'
        r['proposed_changes']={'gold_answer':g['gold_answer'].replace('quarterly in person, or monthly or as needed by phone','quarterly in person, and monthly or as needed by phone'),'gold_passage':g['gold_passage']+' | '+passage('Creve_Coeur_MO__RFP',q)}
    if id=='OTH-18':
        r['status']='needs_correction'
        refs=[('LACERS','LACERS intends to award a full-service three-year contract that could become eligible for up to two one-year contract extensions'),('Boston__','The term of the contract shall be for five (5) years. The Board reserves the right to extend this contract for an additional one (1) or two (2) years without further advertising.'),('COAERS__COAERS_Actuarial','COAERS seeks to negotiate and execute a five-year Master Services Agreement'),('Illinois_SRS','a five-year contract beginning July 1, 2024, and ending on June 30, 2029.'),('Stoneham','The term of the contract shall not exceed seven (7) years'),('KCERA__RFP_2024','The contract term shall be for a period of one year beginning on the date of final contract execution.'),('St_Louis','The initial term of the contract awarded pursuant to this RFP will be for a one-time period, with the PRS-STL retaining the option to renew the contract.'),('AVFPD','Actuarial fees associated with optional extensions exercised by AVFPD will be negotiated at the time of contract extension.')]
        r['proposed_changes']={'gold_answer':b['blind_answer'],'gold_source_file':';'.join(source(k).name for k,q in refs),'gold_passage':' | '.join(passage(k,q) for k,q in refs)}
    out.append(r)
assert len(out)==40 and set(r['id'] for r in out)==set(gold)
assert hashlib.sha256(bp.read_bytes()).hexdigest()==before
(AUDIT/'compare_3.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in out),encoding='utf-8')
counts=Counter(r['status'] for r in out)
summary=f'''# Independent blind verification — batch 3

Completed all 40 assigned records. Stage A saved every five answers, then completed the legacy DOC corpus checks before any frozen golds were opened. Stage B compared all 40 against the UTF-8 BOM frozen CSV and revisited discrepancies. No other verifier output, source-question edit, Sirchmunk call, paid API or evaluation experiment was used.

Counts: {counts['verified']} verified; {counts['needs_correction']} needs correction; {counts['ambiguous']} ambiguous; {counts['unverifiable']} unverifiable.

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

Final blind-answer SHA-256 (unchanged during comparison): `{before}`.
'''
(AUDIT/'batch_3_summary.md').write_text(summary,encoding='utf-8')
print(dict(counts))
print('Wrote compare_3.jsonl and batch_3_summary.md; blind answers unchanged.')
