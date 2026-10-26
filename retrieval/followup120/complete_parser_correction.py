"""Run the corrected parser comparison, refresh source checks and collect artifacts."""
import json
import sys
from pathlib import Path
from supervise import HERE,BASE,REMOTE,CONTAINER,command,deploy,collect,collect_runs,remote_stage,event


def main():
    assert (HERE/'pipeline_complete.json').exists(), 'Finish and collect the initial source checks first'
    # Preserve the first comparison and pool before replacing the main P/P0 results.
    archive=HERE/'parser_initial_invalid'
    if not archive.exists():
        archive.mkdir()
        for src,dst in [('reports/stage_diagnostics.json','stage_diagnostics.json'),
                        ('review_inputs/manifest.json','review_manifest.json'),
                        ('review_inputs/jobs.json','review_jobs.json'),
                        ('scoring_freeze.json','scoring_freeze.json')]:
            (archive/dst).write_bytes((HERE/src).read_bytes())
    deploy(HERE/'parser_replay_corrected.py',REMOTE+'/parser_replay_corrected.py')
    deploy(HERE/'parser_correction_freeze.json',REMOTE+'/parser_correction_freeze.json')
    remote_stage('parser_corrected','parser_replay_corrected.py',['run'],transport=False)
    collect(REMOTE+'/parser_initial_invalid/.',archive)
    collect_runs(['P0','P'])
    for name in ['parser_validation.json','parser_progress.jsonl','parser_complete.json',
                 'parser_correction_smoke.json','parser_async_trace.jsonl']:
        collect(REMOTE+'/'+name,HERE/name)
    event(action='corrected_parser_collected')
    command([sys.executable,str(HERE/'prepare_support.py')])
    # Copy contents into the existing remote input folder, without nesting it.
    command(['docker','cp',str(HERE/'review_inputs')+'/.',f'{CONTAINER}:{REMOTE}/review_inputs'],capture_output=True)
    code='''from pathlib import Path
import json
r=Path('/retrieval_followup_20261023'); out=r/'support_reviews'
jobs=json.loads((r/'review_inputs/jobs.json').read_text()); upgrades=[]; carried=0
for j in jobs:
 p=out/(j['id']+'.json')
 if not p.exists(): continue
 old=json.loads(p.read_text())
 assert old['job']['text_hash']==j['text_hash'] and old['job']['question']==j['question'] and old['job']['acceptance']==j['acceptance']
 if j['second_check_required'] and len(old['reviews'])<2:
  saved=out/'superseded_parser'; saved.mkdir(exist_ok=True)
  p.rename(saved/p.name)
  old['job']=j; old['support']=None
  pending=out/'pending'; pending.mkdir(exist_ok=True)
  (pending/p.name).write_text(json.dumps(old,ensure_ascii=False,indent=2),encoding='utf-8')
  upgrades.append(j['id'])
 else: carried+=1
value=dict(jobs=len(jobs),carried_completed=carried,additional_jobs=len(jobs)-carried,additional_second_checks=len(upgrades),upgraded_ids=upgrades)
(r/'parser_correction_review_refresh.json').write_text(json.dumps(value,indent=2))
print(json.dumps(value))
'''
    command(['docker','exec',CONTAINER,'python','-c',code])
    remote_stage('source_checks_corrected','check_support.py')
    collect(REMOTE+'/support_reviews/.',HERE/'support_reviews')
    for name in ['support_complete.json','transport_events.jsonl','parser_correction_review_refresh.json']:
        collect(REMOTE+'/'+name,HERE/name)
    event(action='corrected_source_checks_collected')
    (HERE/'parser_correction_complete.json').write_text(json.dumps(dict(
        corrected_parser_and_source_checks_collected=True,final_adjudication_and_reporting='next')),encoding='utf-8')


if __name__=='__main__': main()
