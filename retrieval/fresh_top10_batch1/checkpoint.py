"""Record completed-result hashes before a transport-only resume."""
import argparse
import time
from common import HERE,save,sha

def main(name):
    assert name.isidentifier()
    target=HERE/'recovery'/(name+'.json')
    assert not target.exists()
    files=sorted((HERE/'runs').glob('*/queries/*.json'))
    save(target,dict(reason='Connection failure; resume pending tasks with unchanged settings.',
        created_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),completed=len(files),
        files={p.relative_to(HERE).as_posix():sha(p) for p in files}))
    print('Checkpoint:',len(files),'completed results')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('name');main(p.parse_args().name)
