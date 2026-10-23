"""Host-side replay of the separate source-support checks."""
import argparse
import json
import subprocess
import sys
from pathlib import Path

HERE=Path(__file__).resolve().parent


def main(remote):
    config=json.loads((HERE/'inputs/config.json').read_text(encoding='utf-8'))
    container=config['container']
    def run(args,**kwargs):
        subprocess.run(args,check=True,**kwargs)
    run([sys.executable,str(HERE/'build_reviews.py')])
    run(['docker','exec',container,'mkdir','-p',remote])
    for name in ['runtime.py','review_support.py']:
        run(['docker','cp',str(HERE/name),f'{container}:{remote}/{name}'])
    run(['docker','cp',str(HERE/'review_inputs'),f'{container}:{remote}/review_inputs'])
    with (HERE/'execution_logs/support_replay.log').open('w',encoding='utf-8') as log:
        run(['docker','exec','-e',f"LLM_MODEL_NAME={config['model']}",container,'python',
             remote+'/review_support.py','--root',remote,'--model',config['model']],
             stdout=log,stderr=subprocess.STDOUT)
    (HERE/'support_reviews').mkdir(exist_ok=True)
    run(['docker','cp',f'{container}:{remote}/support_reviews/.',str(HERE/'support_reviews')])


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--root',default='/retrieval_support_replay')
    main(parser.parse_args().root)
