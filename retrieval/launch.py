"""Host launcher for the basic 120-question document retrieval test."""
import json
import os
import subprocess
from pathlib import Path

HERE=Path(__file__).resolve().parent


def command(args,**kwargs):
    return subprocess.run(args,check=True,creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0,**kwargs)


def main():
    config=json.loads((HERE/'inputs/config.json').read_text())
    container,remote=config['container'],config['container_root']
    command(['docker','exec',container,'mkdir','-p',remote+'/inputs'])
    for name in ['runtime.py','basic_run.py','test_runtime.py']:
        command(['docker','cp',str(HERE/name),f'{container}:{remote}/{name}'])
    for name in ['queries.json','corpus.json','config.json']:
        command(['docker','cp',str(HERE/'inputs'/name),f'{container}:{remote}/inputs/{name}'])
    (HERE/'execution_logs').mkdir(exist_ok=True)
    base=['docker','exec','-e',f"LLM_MODEL_NAME={config['model']}",container,'python']
    command(base+[remote+'/test_runtime.py'])
    with (HERE/'execution_logs/basic120.log').open('w',encoding='utf-8') as log:
        command(base+[remote+'/basic_run.py','prepare','--root',remote],stdout=log,stderr=subprocess.STDOUT)
        print('Preflight passed; starting all 120 queries.',flush=True)
        command(base+[remote+'/basic_run.py','run','--root',remote],stdout=log,stderr=subprocess.STDOUT)
    (HERE/'results').mkdir(exist_ok=True)
    command(['docker','cp',f'{container}:{remote}/results/.',str(HERE/'results')])
    command(['docker','cp',f'{container}:{remote}/inputs/directory_scan.json',str(HERE/'inputs/directory_scan.json')])
    print('All retrieval artifacts copied back.',flush=True)


if __name__=='__main__':
    main()
