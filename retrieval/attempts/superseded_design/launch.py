"""Run six isolated complete repetitions and copy their artifacts back to this checkout."""
import concurrent.futures
import json
import os
import subprocess
import time
from pathlib import Path

HERE=Path(__file__).resolve().parent
CONFIG=json.loads((HERE/'inputs/config.json').read_text())
REMOTE=CONFIG['container_root']


def worker(name):
    with (HERE/'execution_logs'/f'{name}.log').open('w',encoding='utf-8') as log:
        command=['docker','exec','-e',f"LLM_MODEL_NAME={CONFIG['model']}",CONFIG['container'],
                 'python',f'{REMOTE}/container_run.py','run','--name',name]
        p=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,
                           creationflags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0)
        result=dict(run=name,pid=p.pid,exit_code=p.wait())
        print(json.dumps(result),flush=True)
        return result


def main():
    (HERE/'execution_logs').mkdir(exist_ok=True)
    started=time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=CONFIG['workers']) as pool:
        results=list(pool.map(worker,CONFIG['launch_order']))
    summary=dict(elapsed_s=round(time.time()-started,2),workers=results)
    (HERE/'execution_logs/launch_result.json').write_text(json.dumps(summary,indent=2))
    for name in ['runs','parsed','source_snapshot','preflight.json','preflight_calls.jsonl']:
        subprocess.run(['docker','cp',f"{CONFIG['container']}:{REMOTE}/{name}",str(HERE/name)],check=True)
    if any(r['exit_code'] for r in results):
        raise SystemExit('A worker failed; inspect execution logs before resuming')


if __name__=='__main__':
    main()
