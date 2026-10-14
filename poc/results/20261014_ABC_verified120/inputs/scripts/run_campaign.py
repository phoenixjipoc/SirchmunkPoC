"""Run one stage of the authorized A -> B -> C campaign and preserve artifacts."""
import argparse
import csv
import hashlib
import json
import shutil
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from export_clusters import export

POC=Path(__file__).resolve().parent
CONFIGS={'A':{'top_k':10,'reuse':False},'B':{'top_k':5,'reuse':False},'C':{'top_k':10,'reuse':True}}


def timestamp():
    return datetime.now(timezone(timedelta(hours=8))).isoformat(timespec='seconds')


def read_csv(path):
    with path.open(encoding='utf-8-sig',newline='') as f:
        return list(csv.DictReader(f))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def event(root,kind,**details):
    rec={'time':timestamp(),'event':kind,**details}
    with (root/'events.jsonl').open('a',encoding='utf-8') as f:
        f.write(json.dumps(rec,ensure_ascii=False)+'\n')
    with (root/'test_process.md').open('a',encoding='utf-8') as f:
        f.write(f"\n- {rec['time']} `{kind}`："+json.dumps(details,ensure_ascii=False)+'\n')
    print(json.dumps(rec,ensure_ascii=False),flush=True)


def initialize(root):
    manifest_path=root/'campaign.json'
    if manifest_path.exists():
        return json.loads(manifest_path.read_text(encoding='utf-8'))
    pre=json.loads((root/'preflight.json').read_text(encoding='utf-8'))
    assert pre['corpus_hashes_match_audit'] and pre['host_hashes_match_audit']
    inputs=root/'inputs'
    inputs.mkdir(parents=True,exist_ok=True)
    source=POC/'questions/questions_verified.csv'
    questions=read_csv(source)
    assert len(questions)==120 and len({q['id'] for q in questions})==120
    assert all(q['verify_status'] in ('verified','corrected') for q in questions)
    positions={q['id']:i for i,q in enumerate(questions)}
    pairs={}
    for q in questions:
        if q['pair_id']: pairs.setdefault(q['pair_id'],{})[q['type']]=q
    assert len(pairs)==15
    assert all(positions[p['pair_b']['id']]==positions[p['pair_a']['id']]+1 for p in pairs.values())
    shutil.copyfile(source,inputs/'questions.csv')
    shutil.copyfile(POC/'questions/verification/compare_audit_20261014.jsonl',inputs/'audit_acceptance.jsonl')
    shutil.copyfile(POC/'questions/verification/audit_20261014/source_inventory.json',inputs/'source_inventory.json')
    scripts={}
    for relative in ['run_eval.py','harness/sirch_runner.py','judge.py','export_clusters.py','run_campaign.py','campaign_preflight.py']:
        file=POC/relative
        dest=inputs/'scripts'/relative
        dest.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(file,dest)
        scripts[relative]=digest(file)
    manifest={'id':root.name,'created':timestamp(),'state':'prepared','model':pre['model'],
        'sirchmunk_version':pre['version'],'mode':'DEEP','tier':'S','documents':81,'questions':120,
        'question_sha256':digest(inputs/'questions.csv'),'scripts':scripts,'configs':CONFIGS,
        'cluster_similarity_threshold':0.85,'question_order':'frozen CSV order; every pair_a immediately before pair_b',
        'rga_cache':'shared /poc_cache/rga_S, locally prewarmed before A',
        'cluster_isolation':'new empty work path for each stage; C reuses only clusters built earlier in C',
        'parser_limitations':pre['parser_limitations'],'stages':{}}
    manifest_path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    (root/'test_process.md').write_text(
        '# A → B → C 测试过程\n\n全部使用核验后的 120 题、81 份 raw 文档、DEEP、串行请求。'
        '\n\n|阶段|top_k|知识簇复用|\n|---|---:|---|\n|A|10|关闭|\n|B|5|关闭|\n|C|10|开启，阈值 0.85|\n'
        '\n每轮空知识簇起步，保持题序、模型与解析缓存条件相同。C 只复用本轮前题产生的簇。'
        '\n\n评分采用冻结参考答案及核验接受标准；错误、拒答与运行异常分开。来源覆盖率不等于答案得到支持。'
        '\n搜索模型与初评模型使用同一已配置端点，存在同模型评分偏差；后续复核另行记录。'
        '\n单次运行仍有模型与采样随机性，对照差异不作为统计显著性的证明。费用以 token 用量记录，不推测金额。'
        '\n\n## 执行记录\n',encoding='utf-8')
    event(root,'prepared',question_sha256=manifest['question_sha256'],parser_limitations=pre['parser_limitations'])
    return manifest


def run_command(root,stage,kind,command):
    event(root,kind+'_started',stage=stage,command=command)
    with (root/stage/(kind+'.log')).open('a',encoding='utf-8') as log:
        proc=subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
                              text=True,encoding='utf-8',errors='replace',bufsize=1)
        for line in proc.stdout:
            log.write(line); log.flush()
            print(line,end='',flush=True)
        code=proc.wait()
    event(root,kind+'_finished',stage=stage,returncode=code)
    if code: raise RuntimeError(f'{kind} failed in stage {stage}; see saved log')


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('campaign_dir',type=Path)
    ap.add_argument('--stage',required=True,choices=CONFIGS)
    ap.add_argument('--resume',action='store_true')
    args=ap.parse_args()
    root=args.campaign_dir.resolve()
    manifest=initialize(root)
    stage=args.stage
    for earlier in list(CONFIGS)[:list(CONFIGS).index(stage)]:
        if manifest['stages'].get(earlier,{}).get('state')!='complete':
            raise RuntimeError(f'Finish {earlier} before {stage}')
    if digest(root/'inputs/questions.csv')!=manifest['question_sha256']:
        raise RuntimeError('Frozen questions changed')
    for relative,expected in manifest['scripts'].items():
        if digest(POC/relative)!=expected:
            raise RuntimeError('Frozen executable changed: '+relative)
    model=subprocess.check_output(['docker','exec','sirchmunk','printenv','LLM_MODEL_NAME'],text=True).strip()
    if model!=manifest['model']: raise RuntimeError('Search model changed since preflight')
    directory=root/stage
    directory.mkdir(exist_ok=True)
    config=CONFIGS[stage]
    run_id=f'{root.name}_{stage}'
    record=manifest['stages'].get(stage,{})
    if record.get('state')=='complete':
        print('Stage already complete; no duplicate calls.'); return
    if record and not args.resume: raise RuntimeError('Existing stage requires --resume')
    record.update(state='running',started=record.get('started',timestamp()),run_id=run_id,**config)
    manifest['stages'][stage]=record
    manifest['state']='running'
    save=lambda:(root/'campaign.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    save()
    try:
        command=[sys.executable,'-u',str(POC/'run_eval.py'),'--tier','S','--mode','DEEP',
                 '--questions',str(root/'inputs/questions.csv'),'--top-k-files',str(config['top_k']),
                 '--sim-threshold','0.85','--output-dir',str(directory)]
        if config['reuse'] is False: command.append('--no-reuse')
        command+=['--resume' if args.resume else '--run-id',run_id]
        if not (directory/'results.csv').exists() or len(read_csv(directory/'results.csv'))!=120:
            run_command(root,stage,'search',command)
        meta=json.loads((directory/'run_meta.json').read_text(encoding='utf-8'))
        if meta.get('state')!='complete': raise RuntimeError('Search stage is incomplete')
        run_command(root,stage,'judge',[sys.executable,'-u',str(POC/'judge.py'),str(directory)])
        rows=read_csv(directory/'results_judged.csv')
        assert len(rows)==120 and len({r['id'] for r in rows})==120
        assert set(r['id'] for r in rows)==set(q['id'] for q in read_csv(root/'inputs/questions.csv'))
        count=export(f'/poc_runs/{run_id}/work/.cache/knowledge/knowledge_clusters.parquet',directory,True)
        record.update(state='complete',finished=timestamp(),clusters_exported=count)
        event(root,'stage_complete',stage=stage,questions=len(rows),clusters=count)
        manifest['state']='complete' if all(manifest['stages'].get(s,{}).get('state')=='complete' for s in CONFIGS) else 'awaiting_next_stage'
    except Exception as exc:
        record.update(state='failed',failure=f'{type(exc).__name__}: {exc}')
        manifest['state']='failed'
        event(root,'stage_failed',stage=stage,error=record['failure'])
        raise
    finally:
        save()


if __name__=='__main__': main()
