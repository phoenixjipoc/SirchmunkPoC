"""Run two fixed-candidate ranking arms; no discovery or answer production."""
import argparse
import asyncio
import inspect
import json
import sys
import time
from collections import Counter
from pathlib import Path
from common import read, save, sha, ordered_ids, apply_order

sys.path.insert(0, str(Path(__file__).parent/'adapter'))
import runtime
from runtime import CheckedChat, ModelMismatch, phase_call, append
runtime.ALLOWED.add('rerank')

def verify(root):
    for name, expected in read(root/'freeze.json')['files'].items():
        assert sha(root/name) == expected, f'Frozen file changed: {name}'
    import sirchmunk
    installed = Path(inspect.getfile(sirchmunk)).parent
    for name, expected in read(root/'inputs/original_preflight.json')['source_hashes'].items():
        assert sha(installed/name) == expected, f'Installed source changed: {name}'
    actual = {p.name: sha(p) for p in Path('/mnt/docs/S').iterdir() if p.is_file()}
    assert actual == {r['file']: r['sha256'] for r in read(root/'inputs/corpus.json')}
    save(root/'environment_validation.json', dict(frozen_files=len(read(root/'freeze.json')['files']),
        corpus_files=len(actual), installed_source_matched=True, all_passed=True))

async def preflight(root, settings):
    chat = CheckedChat(settings['model'], root/'preflight_calls.jsonl', root/'STOP_MODEL_MISMATCH', concurrency=1)
    try:
        response = await phase_call('preflight', chat._async_client.chat.completions.create(
            model=settings['model'], stream=False, messages=[{'role':'user','content':'Reply with exactly OK.'}]))
        assert response.choices[0].message.content.strip() == 'OK'
        assert chat.records[-1]['finish_reason'] == 'stop'
        save(root/'preflight.json', dict(passed=True, request=chat.records[-1]))
    finally:
        await chat.close()

async def one(root, q, group, settings, chat):
    dest = root/'runs'/group/'queries'/(q['id']+'.json')
    if dest.exists():
        return read(dest)
    limit = settings['groups'][group]
    baseline = read(root/'baseline'/(q['id']+'.json'))
    original = [r['file'] for r in baseline['references']]
    paths = {r['file']: r['path'] for r in baseline['references']}
    payload_path = root/'inputs/payloads'/group/(q['id']+'.json')
    payload = read(payload_path)
    by_id = {d['id']: d['file'] for d in payload['documents']}
    output = list(original)
    status = 'skipped_empty' if not original else 'skipped_single'
    if len(by_id) > 1:
        status = 'fallback_original'
        folder = root/'runs'/group/'attempts'/q['id']
        prior = sorted(folder.glob('*.json'))
        if prior and read(prior[-1])['status'] == 'ok':
            output = read(prior[-1])['output_files']
            status = 'ok'
        else:
            for attempt in range(len(prior)+1, settings['max_attempts']+1):
                chat.query_id = q['id']
                started = time.monotonic()
                record = dict(query_id=q['id'], group=group, attempt=attempt, payload_sha256=sha(payload_path))
                try:
                    response = await phase_call('rerank', chat._async_client.chat.completions.create(
                        model=settings['model'], stream=False,
                        messages=[{'role':'system','content':(root/'prompt.txt').read_text(encoding='utf-8')},
                                  {'role':'user','content':json.dumps(payload, ensure_ascii=False)}],
                        **settings['request_parameters']))
                    if response.choices[0].finish_reason != 'stop':
                        raise ValueError('Incomplete response')
                    ids = ordered_ids(json.loads(response.choices[0].message.content), by_id)
                    output = apply_order(original, [by_id[x] for x in ids], limit)
                    record.update(status='ok', output_files=output, response_id=response.id)
                    status = 'ok'
                except ModelMismatch:
                    raise
                except Exception as exc:
                    record.update(status='technical_error', error_type=type(exc).__name__, error=str(exc)[:1500])
                    if type(exc).__name__ in {'AuthenticationError','PermissionDeniedError','NotFoundError'} or 'insufficient_quota' in str(exc):
                        record['fatal'] = True
                record['elapsed_s'] = round(time.monotonic()-started, 3)
                save(folder/f'{attempt}.json', record)
                if record.get('fatal'):
                    raise RuntimeError('Service authorization or configuration error; inspect attempt record')
                if status == 'ok':
                    break
                if attempt < settings['max_attempts']:
                    await asyncio.sleep(5)
    attempts = [read(p) for p in (root/'runs'/group/'attempts'/q['id']).glob('*.json')]
    result = dict(query_id=q['id'], question=q['question'], type=q['type'], pair_id=q['pair_id'], group=group,
        status=status, candidate_limit=limit, candidate_count=len(by_id), baseline_sha256=sha(root/'baseline'/(q['id']+'.json')),
        payload_sha256=sha(payload_path), original_files=original,
        references=[dict(rank=i+1, file=name, path=paths[name]) for i,name in enumerate(output)],
        attempts=len(attempts), elapsed_s=sum(a['elapsed_s'] for a in attempts),
        answer_generated=False, cluster_used=False, evidence_sampling=False)
    save(dest, result)
    append(root/'progress.jsonl', dict(group=group, id=q['id'], status=status, attempts=len(attempts)))
    print(json.dumps(dict(group=group,id=q['id'],status=status,attempts=len(attempts))), flush=True)
    if status == 'fallback_original':
        await preflight(root, settings)
    return result

async def main(root, smoke=False):
    verify(root)
    settings = read(root/'settings.json')
    await preflight(root, settings)
    queries = read(root/'inputs/queries.json')
    chats = {g: CheckedChat(settings['model'],root/'runs'/g/'calls.jsonl',root/'STOP_MODEL_MISMATCH',concurrency=1) for g in settings['groups']}
    start = time.monotonic()
    try:
        for i,q in enumerate(queries[:1] if smoke else queries):
            groups = list(settings['groups'])
            if i % 2:
                groups.reverse()
            for group in groups:
                await one(root,q,group,settings,chats[group])
    finally:
        for chat in chats.values():
            await chat.close()
    if smoke:
        save(root/'smoke.json', dict(passed=True, query_id=queries[0]['id'], included_in_final_run=True))
        return
    for group in settings['groups']:
        rows = [read(p) for p in (root/'runs'/group/'queries').glob('*.json')]
        assert {r['query_id'] for r in rows} == {q['id'] for q in queries}
        save(root/'runs'/group/'complete.json', dict(questions=len(rows),statuses=dict(Counter(r['status'] for r in rows))))
    save(root/'retrieval_complete.json', dict(groups=list(settings['groups']), tasks=240,
        finished_utc=time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),last_process_elapsed_s=round(time.monotonic()-start,3)))

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--root', type=Path, default=Path(__file__).parent)
    p.add_argument('--smoke', action='store_true')
    args = p.parse_args()
    asyncio.run(main(args.root,args.smoke))
