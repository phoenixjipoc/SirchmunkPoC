"""Agent 2 only: assemble post-blind review and validate its own artifacts."""
import csv,json,re,hashlib
from pathlib import Path
from collections import Counter
import sys
sys.stdout.reconfigure(encoding='utf-8')
A=Path(__file__).parent
R=A.parents[3]
norm=lambda s:re.sub(r'\s+',' ',s).strip()
blind_path=A/'blind_answers_2.jsonl'
before=hashlib.sha256(blind_path.read_bytes()).hexdigest()
blind=[json.loads(x) for x in blind_path.read_text(encoding='utf-8').splitlines()]
gold={x['id']:x for x in csv.DictReader((A/'original/questions.csv').open(encoding='utf-8-sig',newline=''))}
cfg=json.loads((A/'agent2_review_config.json').read_text(encoding='utf-8'))
assert len(blind)==40
assert len({r['id'] for r in blind})==40
def text(file):return norm((R/'poc/corpus/text_S'/(file+'.txt')).read_text(encoding='utf-8'))
def span(file,start,end):
    s=text(file);i=s.index(start);j=s.index(end,i)+len(end)
    return s[i:j]
def existing(file,fragment):
    assert norm(fragment) in text(file),(file,fragment)
    return norm(fragment)
rows=[]
for b in blind:
    id=b['id'];g=gold[id];o=cfg['overrides'].get(id,{})
    rows.append(dict(id=id,status=o.get('status','verified'),blind_answer=b['blind_answer'],
        blind_source_file=b['blind_source_file'],note=o.get('note','Independent answer agrees semantically with frozen gold; supporting source passages and locators checked.'),
        evidence=b['evidence']+o.get('append_evidence',[]),proposed_changes=o.get('proposed_changes',{}).copy(),
        acceptance_notes=cfg['acceptance'][id],reviewer='independent_agent_2',verification_method='blind_answer_then_gold_comparison'))
by={r['id']:r for r in rows}
B='Baltimore_BCERS__RFP-Alternatives-Consultant-rev.pdf'
M='Missouri_LAGERS__LAGERS-Private-Consultant-RFP-Final.pdf'
H='Hartford_MERF__file.pdf'
L='LAFPP__RFP-Financial-Statement-Audit-Services-DCFS25-01-with-attachments.pdf'
I='ILPA__ILPA-DDQ-2.0.pdf'
E='ILPA__ILPA-ESG-Assessment-Framework.pdf'
by['INV-23']['proposed_changes']['gold_passage']=gold['INV-23']['gold_passage']+' | '+span(B,'Please state whether you will agree','two (2) two-year options.')+' | '+span(M,'LAGERS plans to enter into an agreement','agreed upon by both parties.')
by['CONS-14']['proposed_changes']['gold_passage']=span(H,'The Proposer shall have been in business','higher insurance coverage.')+' | '+span(H,'All minimum qualifications shall be met','immediate rejection of the proposal.')
by['DDQ-10']['proposed_changes']['gold_passage']=' | '.join([
    existing(I,'19.1 Policy - Understanding your ESG-related policies, governance and oversight'),
    existing(I,'19.2 Fundraising – Establishing your ESG commitments within fund documentation'),
    existing(I,'19.3 Pre-investment – Understanding how you identify material ESG risks and opportunities in your investments'),
    existing(I,"19.4 Post-investment – Understanding how you contribute to your portfolio companies' ESG risk mitigation and value- creation efforts."),
    existing(I,'19.5 Reporting and Disclosure – Understanding how Limited Partners can monitor your ESG performance and ensure the fund is operating within agreed-upon policies and practices, including disclosing material ESG incidents.'),
    existing(I,'19.6 Climate Change'),existing(I,'19.7 Additional Information'),
    existing(I,"How do you manage your management company's (i.e. your own business') internal ESG risks and opportunities?")])
by['XD-17']['proposed_changes']['gold_passage']=gold['XD-17']['gold_passage']+' | '+span(L,'1.22 Standard Provisions','PSC-41 Compliance with California Public Resources Code Section 5164.')
by['DDQ-04']['proposed_changes']['gold_passage']=' | '.join(existing(E,s) for s in ['GP conducts a periodic review (i.e.','every 2-3 years) of its ESG policy','GP reviews its ESG policy annually and can'])

expected=[json.loads(x)['id'] for x in (R/'poc/questions/verification/blind_2.jsonl').read_text(encoding='utf-8-sig').splitlines()]
assert [r['id'] for r in rows]==expected
checks=[]
for row in rows:
    assert row['blind_answer']==next(b['blind_answer'] for b in blind if b['id']==row['id'])
    for ev in row['evidence']:
        assert (R/'poc_docs/S'/ev['file']).is_file(),ev
        fresh=(A/'source_text'/(ev['file']+'.txt')).read_text(encoding='utf-8')
        old=(R/'poc/corpus/text_S'/(ev['file']+'.txt')).read_text(encoding='utf-8')
        q=norm(ev['quote'])
        match=q in norm(fresh) or q in norm(old)
        assert match,(row['id'],'unmatched quote',ev)
        page_ok=None
        if isinstance(ev['page'],int):
            split=re.split(r'\[PDF page (\d+)\]',fresh)
            pages={int(split[i]):norm(split[i+1]) for i in range(1,len(split),2)}
            actual=[p for p,s in pages.items() if q in s]
            page_ok=ev['page'] in actual if actual else None
            assert page_ok is not False,(row['id'],'wrong page',ev,actual)
        checks.append({'id':row['id'],'file':ev['file'],'page':ev['page'],'match':match,'page_match':page_ok})
    p=row['proposed_changes']
    if 'gold_passage' in p:
        names=p.get('gold_source_file',gold[row['id']]['gold_source_file']).split(';')
        for q in p['gold_passage'].split(' | '):
            assert any(norm(q) in text(n) for n in names if n),(row['id'],'proposed passage not verbatim',q)
payload=''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows)
assert '\ufffd' not in payload and '\u00e2\u20ac' not in payload
(A/'compare_2.jsonl').write_text(payload,encoding='utf-8')
assert hashlib.sha256(blind_path.read_bytes()).hexdigest()==before,'Blind file changed!'
counts=dict(Counter(r['status'] for r in rows))
report={'count':len(rows),'statuses':counts,'evidence_count':len(checks),'evidence_matches':sum(x['match'] for x in checks),'wrong_pages':sum(x['page_match'] is False for x in checks),'blind_sha256_before_and_after':before,'checks':checks}
(A/'agent2_validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k!='checks'},ensure_ascii=False,indent=2))
