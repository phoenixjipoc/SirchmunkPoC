"""Collect completed retrieval and support artifacts; preserve obsolete attempts."""
import json
import subprocess
import sys
from pathlib import Path

HERE=Path(__file__).resolve().parent


def main():
    config=json.loads((HERE/'inputs/config.json').read_text(encoding='utf-8'))
    container=config['container']; remote=config['container_root']; support='/retrieval_support_20261023'
    def run(args): subprocess.run(args,check=True)
    check=f"from pathlib import Path; import json; r=Path('{remote}/results/basic120'); s=Path('{support}'); assert (r/'complete.json').exists(); c=json.loads((r/'complete.json').read_text()); assert c['questions']==120; j=json.loads((s/'review_inputs/jobs.json').read_text()); d=json.loads((s/'support_complete.json').read_text()); assert d['document_checks']==len(j); assert all((s/'support_reviews'/(x['id']+'.json')).exists() for x in j); print('Completed artifact sets confirmed')"
    run(['docker','exec',container,'python','-c',check])
    (HERE/'results/basic120').mkdir(parents=True,exist_ok=True)
    (HERE/'support_reviews').mkdir(exist_ok=True)
    run(['docker','cp',f'{container}:{remote}/results/basic120/.',str(HERE/'results/basic120')])
    run(['docker','cp',f'{container}:{remote}/inputs/directory_scan.json',str(HERE/'inputs/directory_scan.json')])
    run(['docker','cp',f'{container}:{support}/support_reviews/.',str(HERE/'support_reviews')])
    run(['docker','cp',f'{container}:{support}/support_complete.json',str(HERE/'support_complete.json')])
    failed=HERE/'attempts/network_interruption/failed_support'
    failed.mkdir(exist_ok=True)
    run(['docker','cp',f'{container}:{support}/failed_reviews/.',str(failed)])
    run([sys.executable,str(HERE/'build_reviews.py')])
    jobs=json.loads((HERE/'review_inputs/jobs.json').read_text(encoding='utf-8'))
    identifiers={j['id'] for j in jobs}
    archive=HERE/'attempts/network_interruption/unused_support'
    archive.mkdir(exist_ok=True)
    moved=[]
    for p in (HERE/'support_reviews').glob('*.json'):
        if p.stem not in identifiers:
            target=archive/p.name
            p.resolve().relative_to(HERE.resolve()); target.resolve().relative_to(HERE.resolve())
            if target.exists():
                assert target.read_bytes()==p.read_bytes()
                p.unlink()
            else: p.rename(target)
            moved.append(p.stem)
    print(json.dumps({'archived_obsolete_checks':moved}))


if __name__=='__main__':
    main()
