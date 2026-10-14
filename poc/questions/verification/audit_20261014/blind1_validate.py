import json, pathlib, re
p=pathlib.Path(__file__).parent
blind=[json.loads(x) for x in (p/'blind_answers_1.jsonl').read_text(encoding='utf-8-sig').splitlines()]
comp=[json.loads(x) for x in (p/'compare_1.jsonl').read_text(encoding='utf-8-sig').splitlines()]
scope=[json.loads(x) for x in (p.parent/'blind_1.jsonl').read_text(encoding='utf-8-sig').splitlines()]
assert len(blind)==len(comp)==len(scope)==40
assert [r['id'] for r in blind]==[r['id'] for r in comp]==[r['id'] for r in scope]
assert len({r['id'] for r in comp})==40
needed={'id','status','blind_answer','blind_source_file','note','evidence','proposed_changes','acceptance_notes','reviewer','verification_method'}
for a,b,q in zip(blind,comp,scope):
    assert needed<=b.keys()
    assert a['question']==q['question']
    assert a['blind_answer']==b['blind_answer']
    assert a['blind_source_file']==b['blind_source_file']
    assert b['status'] in {'verified','needs_correction','ambiguous','unverifiable'}
    assert b['reviewer']=='independent_agent_1'
    assert b['verification_method']=='blind_answer_then_gold_comparison'
    assert isinstance(b['proposed_changes'],dict)
    for e in b['evidence']:
        assert {'file','page','quote'}<=e.keys()
        assert pathlib.Path('poc_docs/S',e['file']).exists()
    if 'gold_passage' in b['proposed_changes']:
        corp=[pathlib.Path('poc/corpus/text_S',f+'.txt').read_text(encoding='utf-8-sig') for f in a['blind_source_file'].split(';')]
        for frag in b['proposed_changes']['gold_passage'].split(' | '):
            assert any(frag in text for text in corp), (b['id'],'proposed passage not verbatim',frag)
counts={s:sum(r['status']==s for r in comp) for s in ['verified','needs_correction','ambiguous','unverifiable']}
print(json.dumps({'rows':len(comp),'counts':counts,'checks':'ID alignment, blind answer preservation, schema, source-file existence, proposed passage fragments verbatim in existing corpus all passed'},indent=2))
