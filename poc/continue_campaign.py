"""Continue the authorized campaign after the already-running A stage.

Waits for A, checks/reviews its scores, then runs B and C serially with reviews
between stages so review API requests do not compete with search latency tests.
"""
import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

from run_campaign import event

POC=Path(__file__).resolve().parent


def invoke(root,name,command):
    event(root,name+'_started',command=command)
    with (root/(name+'.log')).open('a',encoding='utf-8') as log:
        proc=subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
                              text=True,encoding='utf-8',errors='replace',bufsize=1)
        for line in proc.stdout:
            log.write(line);log.flush();print(line,end='',flush=True)
        code=proc.wait()
    event(root,name+'_finished',returncode=code)
    if code:raise RuntimeError(name+' failed; partial output preserved')


def main():
    ap=argparse.ArgumentParser();ap.add_argument('campaign_dir',type=Path);args=ap.parse_args();root=args.campaign_dir.resolve()
    event(root,'continuation_waiting_for_A')
    while True:
        try:
            state=json.loads((root/'campaign.json').read_text(encoding='utf-8'))['stages'].get('A',{}).get('state')
        except json.JSONDecodeError:
            time.sleep(1);continue
        if state=='complete':break
        if state=='failed':raise RuntimeError('A failed; B/C will not start')
        time.sleep(20)
    for stage in ('A','B','C'):
        if stage!='A':
            manifest=json.loads((root/'campaign.json').read_text(encoding='utf-8'))
            record=manifest['stages'].get(stage,{})
            if record.get('state')!='complete':
                command=[sys.executable,'-u',str(POC/'run_campaign.py'),str(root),'--stage',stage]
                if record:command.append('--resume')
                invoke(root,'stage_'+stage,command)
        invoke(root,'review_'+stage,[sys.executable,'-u',str(POC/'review_campaign_stage.py'),str(root/stage)])
        invoke(root,'report_after_'+stage,[sys.executable,'-u',str(POC/'campaign_report.py'),str(root)])
    event(root,'all_stages_exported_pending_coordinator_disagreements')


if __name__=='__main__':main()
