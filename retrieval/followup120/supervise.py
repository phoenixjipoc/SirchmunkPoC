"""Host-side one-shot continuation, collection and separate source checking."""
import hashlib
import json
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

HERE=Path(__file__).resolve().parent
BASE=HERE.parent
REMOTE='/retrieval_followup_20261023'
CONTAINER='sirchmunk'
FLAGS=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0


def run(args,**kw):
    return subprocess.run(args,creationflags=FLAGS,**kw)


def command(args,**kw):
    return run(args,check=True,**kw)


def event(**kw):
    value=dict(time_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),**kw)
    with (HERE/'supervisor_events.jsonl').open('a',encoding='utf-8') as f: f.write(json.dumps(value)+'\n')
    print(json.dumps(value),flush=True)


def deploy(local,remote):
    command(['docker','cp',str(local),f'{CONTAINER}:{remote}'],capture_output=True)


def collect(remote,local):
    local.parent.mkdir(parents=True,exist_ok=True)
    command(['docker','cp',f'{CONTAINER}:{remote}',str(local)],capture_output=True)


def refresh_dns():
    ips=sorted({x[4][0] for x in socket.getaddrinfo('api.openai.com',443,family=socket.AF_INET)})
    data=dict(host='api.openai.com',addresses=ips,resolved_unix=time.time())
    (HERE/'transport_dns.json').write_text(json.dumps(data,indent=2),encoding='utf-8')
    deploy(HERE/'transport_dns.json',REMOTE+'/transport_dns.json')
    event(action='host_dns_refreshed',addresses=ips)


def pending_groups():
    code="from pathlib import Path; import json; r=Path('/retrieval_followup_20261023'); print(json.dumps([g for g in ['R2','R3','S','D'] if not (r/'runs'/g/'complete.json').exists()]))"
    p=command(['docker','exec',CONTAINER,'python','-c',code],capture_output=True,text=True,encoding='utf-8')
    return json.loads(p.stdout)


def remote_stage(name,script,extra=(),transport=True):
    for attempt in range(1,9):
        if transport:
            try: refresh_dns()
            except socket.gaierror as exc:
                event(action='host_dns_retry',stage=name,error=str(exc))
                time.sleep(30)
                continue
        current_extra=extra
        if script=='experiment.py':
            remaining=pending_groups()
            if not remaining: return
            current_extra=['--groups',*remaining]
        log=HERE/'execution_logs'/f'{name}_{int(time.time())}_{attempt}.log'
        args=['docker','exec','-e','LLM_MODEL_NAME=gpt-6-sol',CONTAINER,'python']
        if transport: args += [REMOTE+'/transport_bootstrap.py',script]
        else: args += [REMOTE+'/'+script]
        args += ['--root',REMOTE,*current_extra]
        event(action='stage_started',stage=name,attempt=attempt,log=log.name)
        with log.open('w',encoding='utf-8') as f:
            p=run(args,stdout=f,stderr=subprocess.STDOUT)
        event(action='stage_exited',stage=name,attempt=attempt,exit_code=p.returncode)
        if p.returncode==0: return
        tail=log.read_text(encoding='utf-8',errors='replace')[-24000:]
        if any(s in tail for s in ['ModelMismatch','STOP_MODEL_MISMATCH','AuthenticationError','PermissionDeniedError']):
            raise RuntimeError(f'{name}: identity or authorization failure; see {log.name}')
        if not any(s in tail for s in ['APIConnectionError','APITimeoutError','socket.gaierror','ConnectError']):
            raise RuntimeError(f'{name}: non-network failure; see {log.name}')
        event(action='network_recovery_wait',stage=name,seconds=30)
        time.sleep(30)
    raise RuntimeError(f'{name}: recovery limit reached')


def collect_retrieval():
    (HERE/'runs').mkdir(exist_ok=True)
    collect(REMOTE+'/runs/.',HERE/'runs')
    for name in ['progress.jsonl','retrieval_complete.json','transport_events.jsonl']:
        collect(REMOTE+'/'+name,HERE/name)


def main():
    remaining=pending_groups()
    if remaining: remote_stage('retrieval','experiment.py',['--groups',*remaining])
    assert not pending_groups(), 'Not all four retrieval stages completed'
    collect_retrieval()
    event(action='all_retrieval_collected')
    for name in ['legacy_adapter.py','parser_replay.py','parser_freeze.json']:
        deploy(HERE/name,REMOTE+'/'+name)
    remote_stage('parser','parser_replay.py',transport=False)
    collect(REMOTE+'/runs/.',HERE/'runs')
    for name in ['parser_validation.json','parser_progress.jsonl','parser_complete.json','legacy_rga.json']:
        collect(REMOTE+'/'+name,HERE/name)
    event(action='parser_collected')
    command([sys.executable,str(HERE/'prepare_support.py')])
    event(action='source_check_jobs_prepared',manifest=json.loads((HERE/'review_inputs/manifest.json').read_text(encoding='utf-8')))
    deploy(BASE/'review_support.py',REMOTE+'/adapter/review_support.py')
    deploy(HERE/'check_support.py',REMOTE+'/check_support.py')
    deploy(HERE/'review_inputs',REMOTE+'/review_inputs')
    remote_stage('source_checks','check_support.py')
    collect(REMOTE+'/support_reviews',HERE/'support_reviews')
    for name in ['support_complete.json','transport_events.jsonl']:
        collect(REMOTE+'/'+name,HERE/name)
    event(action='source_checks_collected')
    (HERE/'pipeline_complete.json').write_text(json.dumps(dict(finished_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),
         source_check_adjudication_and_final_reporting='next')),encoding='utf-8')


if __name__=='__main__': main()
