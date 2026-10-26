"""Collect completed container artifacts without parsing caches or live state."""
import argparse
import os
import subprocess
from common import HERE

REMOTE='/retrieval_fresh_top10_batch1_20261026'
FLAGS=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0

def command(args):
    return subprocess.run(args,check=True,creationflags=FLAGS,capture_output=True,text=True,encoding='utf-8')

def copy(name,directory=False):
    target=HERE/name
    if directory:
        target.mkdir(parents=True,exist_ok=True)
        source=REMOTE+'/'+name+'/.'
    else:
        target.parent.mkdir(parents=True,exist_ok=True)
        source=REMOTE+'/'+name
    command(['docker','cp','sirchmunk:'+source,str(target)])

def main(stage):
    marker='retrieval_complete.json' if stage=='results' else 'support_complete.json'
    command(['docker','exec','sirchmunk','test','-f',REMOTE+'/'+marker])
    if stage=='results':
        for folder in ['inputs','runs','baseline','results','recovery']:copy(folder,True)
        for name in ['preflight.json','preflight_calls.jsonl','scan_freeze.json','rerank_freeze.json',
            'fresh_retrieval_complete.json','retrieval_complete.json']:copy(name)
    else:
        copy('support_reviews',True);copy('support_complete.json')
    print('Collection completed:',stage)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('stage',choices=['results','reviews']);main(p.parse_args().stage)
