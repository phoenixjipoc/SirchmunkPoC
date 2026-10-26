"""Frozen retrieval repeats and directory-coverage comparison; container side."""
import argparse
import asyncio
import hashlib
import json
import shutil
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'adapter'))
from runtime import CheckedChat, ModelMismatch, phase_call, append
from basic_run import one, save, DocumentSearch
from sirchmunk.scan.dir_scanner import FileCandidate, ScanResult



def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(root):
    freeze = read(root / 'freeze.json')
    for name, expected in {**freeze['files'], **freeze.get('publication_files', {})}.items():
        assert digest(root / name) == expected, f'Changed frozen input: {name}'
    actual = {p.name:digest(p) for p in Path('/mnt/docs/S').iterdir() if p.is_file()}
    assert actual == {r['file']:r['sha256'] for r in read(root/'inputs/corpus.json')}
    import sirchmunk, inspect
    installed = Path(inspect.getfile(sirchmunk)).parent
    for name, expected in read(root/'inputs/original_preflight.json')['source_hashes'].items():
        assert digest(installed/name) == expected, f'Installed source changed: {name}'


async def controlled(q, root, chat, group):
    old = read(root/'baseline'/(q['id']+'.json'))
    raw = read(root/'inputs/directory_scan.json')
    record = dict(query_id=q['id'],question=q['question'],type=q['type'],pair_id=q['pair_id'],
                  group=group,references=[],evidence_sampling=False,answer_generated=False,cluster_used=False,
                  baseline_sha256=digest(root/'baseline'/(q['id']+'.json')))
    start = time.monotonic()
    chat.query_id = q['id']
    before = len(chat.records)
    try:
        if group == 'D':
            search = DocumentSearch(chat,root/'work/D')
            scan = ScanResult(candidates=[FileCandidate(**c) for c in raw['candidates']],
                              total_files=raw['total_files'],total_dirs=raw['total_dirs'])
            original = search._dir_scanner._build_rank_prompt
            def capture(*args, **kwargs):
                prompt = original(*args, **kwargs)
                record['directory_prompt'] = prompt
                return prompt
            search._dir_scanner._build_rank_prompt = capture
            dirs = await phase_call('directory',search._rank_dir_scan_candidates(q['question'],scan,top_k=81))
            chat.ensure_running()
            merged = search._merge_file_paths(old['keyword_files'],[],dirs)
            record.update(keyword_files=old['keyword_files'],directory_files=dirs,merged_files=merged,
                          directory_ranking=[c.to_dict() for c in scan.ranked_candidates])
            files = merged[:10]
        else:
            raise ValueError(group)
        bad = [r for r in chat.records[before:] if r['status']!='ok' or r.get('finish_reason')!='stop']
        record['status'] = 'call_error' if bad else ('ok' if files else 'empty_retrieval')
        record['references'] = [dict(rank=i+1,file=Path(p).name,path=p) for i,p in enumerate(files)]
    except ModelMismatch:
        raise
    except Exception as exc:
        record.update(status='technical_error',error=f'{type(exc).__name__}: {exc}')
    finally:
        record.update(elapsed_s=round(time.monotonic()-start,3),calls=len(chat.records)-before,
                      usage={k:sum(r.get('usage',{}).get(k,0) or 0 for r in chat.records[before:])
                             for k in ['prompt_tokens','completion_tokens','total_tokens']})
    return record


async def main(root, groups):
    if not groups or not set(groups) <= {'R2','R3','D'}:
        raise ValueError('Choose only R2, R3 or D')
    verify(root)
    settings = read(root/'settings.json')
    queries = read(root/'inputs/queries.json')
    assert len(queries)==120
    for group in groups:
        output = root/'runs'/group
        output.mkdir(parents=True,exist_ok=True)
        work = root/'work'/group
        (work/'inputs').mkdir(parents=True,exist_ok=True)
        (work/'cache').mkdir(exist_ok=True)
        if not (work/'cache/rga').exists():
            (work/'cache/rga').symlink_to(settings['rga_cache'],target_is_directory=True)
        for name in ['queries.json','directory_scan.json']:
            shutil.copyfile(root/'inputs'/name,work/'inputs'/name)
        config = read(root/'inputs/original_config.json')
        config['seeds'] = [settings['seeds'].get(group,17011)]
        save(work/'inputs/config.json',config)
        chat = CheckedChat(settings['model'],output/'calls.jsonl',root/'STOP_MODEL_MISMATCH')
        pre = await phase_call('preflight',chat.achat([{'role':'user','content':'Reply with exactly OK.'}]))
        assert pre.content.strip()=='OK', 'Preflight failed'
        start = time.monotonic()
        for i,q in enumerate(queries):
            dest = output/'queries'/(q['id']+'.json')
            if dest.exists() and read(dest)['status'] in {'ok','empty_retrieval'}:
                continue
            existing = list((output/'attempts'/q['id']).glob('*.json'))
            result = None
            for attempt in range(len(existing)+1,settings['max_attempts']+1):
                try:
                    if group in {'R2','R3'}:
                        result = await asyncio.wait_for(one(q,work,chat,config),config['query_timeout_s'])
                        result['group'] = group
                    else:
                        result = await asyncio.wait_for(controlled(q,root,chat,group),config['query_timeout_s'])
                except ModelMismatch:
                    raise
                except TimeoutError:
                    result = dict(query_id=q['id'],question=q['question'],type=q['type'],pair_id=q['pair_id'],group=group,
                                  status='timeout',references=[],elapsed_s=config['query_timeout_s'],
                                  evidence_sampling=False,answer_generated=False,cluster_used=False)
                result['attempt'] = attempt
                save(output/'attempts'/q['id']/f'{attempt}.json',result)
                save(dest,result)
                progress = dict(group=group,index=i+1,total=120,id=q['id'],status=result['status'],
                                attempt=attempt,seconds=result['elapsed_s'],references=len(result['references']))
                append(root/'progress.jsonl',progress)
                print(json.dumps(progress),flush=True)
                if result['status'] in {'ok','empty_retrieval'}:
                    break
                await asyncio.sleep(5)
                chat.query_id = q['id']+':recovery_check'
                check = await phase_call('preflight',chat.achat([{'role':'user','content':'Reply with exactly OK.'}]))
                if check.content.strip()!='OK':
                    raise RuntimeError('Recovery endpoint check failed; stopping before further queries')
            if result is None and dest.exists():
                result=read(dest)
            if result is None:
                raise RuntimeError('Missing final attempt record')
        await chat.close()
        rows = [read(p) for p in (output/'queries').glob('*.json')]
        save(output/'complete.json',dict(questions=len(rows),elapsed_s=round(time.monotonic()-start,3),
             statuses={s:sum(r['status']==s for r in rows) for s in {r['status'] for r in rows}}))
    save(root/'retrieval_complete.json',dict(groups=groups,finished_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())))


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--root',type=Path,default=Path('/retrieval_followup_20261023'))
    parser.add_argument('--groups',nargs='+',choices=['R2','R3','D'],default=['R2','R3','D'])
    args=parser.parse_args()
    asyncio.run(main(args.root,args.groups))
