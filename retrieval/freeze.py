"""Freeze corpus identities, questions and retrieval acceptance scope on the host."""
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HERE = ROOT / 'retrieval'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    inputs = HERE / 'inputs'
    inputs.mkdir(exist_ok=True)
    rows = list(csv.DictReader((ROOT / 'poc/questions/questions_verified.csv').open(encoding='utf-8-sig')))
    assert len(rows) == 120 and len({r['id'] for r in rows}) == 120
    queries, standards = [], []
    for r in rows:
        queries.append({k: r[k] for k in ('id', 'question', 'type', 'pair_id')})
        sources = [s.strip() for s in r['gold_source_file'].split(';') if s.strip() and s.strip() != 'NOT IN CORPUS']
        required = sources.copy()
        optional = []
        if r['id'] == 'INV-24':
            optional = [s for s in required if s.startswith('Arizona_PSPRS__')]
            required = [s for s in required if s not in optional]
        scope = 'negative' if r['type'] == 'unanswerable' else ('single_document' if len(sources) == 1 else 'required_combination')
        if r['id'] == 'DDQ-11':
            scope = 'thematic_examples'
        standards.append(dict(queries[-1], gold_answer=r['gold_answer'], gold_passage=r['gold_passage'],
                              acceptance=r['verify_note'].split('Acceptance:')[-1].strip(),
                              source_audit_note=r['verify_note'], known_supporting_sources=sources,
                              required_sources=required, optional_sources=optional, scope=scope))
    originals = [{ 'file': p.name, 'bytes': p.stat().st_size, 'sha256': digest(p)}
                 for p in sorted((ROOT / 'poc_docs/S').iterdir()) if p.is_file()]
    assert len(originals) == 81
    audit = json.loads((ROOT / 'poc/questions/verification/audit_20261014/source_inventory.json').read_text())
    assert {r['file']:r['sha256'] for r in originals} == {r['file']:r['sha256'] for r in audit}
    config = dict(model='gpt-6-sol', corpus='/mnt/docs/S', container='sirchmunk',
                  container_root='/retrieval_basic_20261023_v2', repetitions=1, seeds=[17011],
                  groups={'basic120':10}, query_timeout_s=300, request_timeout_s=120,
                  requests_per_process=3, workers=1, knowledge_reuse=False, final_answer=False,
                  directory_candidates=20, max_depth=5, evidence_sampling=False,
                  questions_sha256=digest(ROOT / 'poc/questions/questions_verified.csv'),
                  launch_order=['basic120'])
    for name, value in [('queries',queries),('standards',standards),('corpus',originals),('config',config)]:
        (inputs / f'{name}.json').write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (inputs / 'freeze_hashes.json').write_text(json.dumps({name:digest(inputs/name)
        for name in ['queries.json','standards.json','corpus.json','config.json']},indent=2)+'\n')
    print(json.dumps({'questions':len(rows),'documents':len(originals),'scopes':{s:sum(x['scope']==s for x in standards) for s in set(x['scope'] for x in standards)}}))


if __name__ == '__main__':
    main()
