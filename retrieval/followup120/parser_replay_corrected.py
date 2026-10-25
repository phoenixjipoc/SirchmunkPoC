"""Correct the asynchronous adapter hook and control file ordering in both arms."""
import argparse
import asyncio
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0,str(Path(__file__).parent/'adapter'))
from basic_run import DocumentSearch,save
from runtime import append
from sirchmunk.retrieve.text_retriever import GrepRetriever
import parser_replay


def install(root,stage):
    original=GrepRetriever._run_rga_async
    async def traced(args,json_output=True,timeout=60.0):
        cache=next(a.split('=',1)[1] for a in args if a.startswith('--rga-cache-path='))
        variant=Path(cache).name
        assert variant in {'P0','P'}, variant
        assert Path(cache).is_relative_to(root)
        flags=['--sort=path']
        if variant=='P': flags.append(f'--rga-config-file={root}/legacy_rga.json')
        actual=flags+list(args)
        result=await original(args=actual,json_output=json_output,timeout=timeout)
        events=result['stdout'] if isinstance(result['stdout'],list) else []
        files=sorted({e['data']['path']['text'] for e in events if e.get('type')=='match'})
        append(root/'parser_async_trace.jsonl',dict(stage=stage,variant=variant,args=actual,
               returncode=result['returncode'],matched_files=files,stderr=result['stderr']))
        return result
    GrepRetriever._run_rga_async=staticmethod(traced)
    return original


async def smoke(root):
    original=install(root,'smoke')
    rows=[]
    try:
        for variant in ['P0','P']:
            search=DocumentSearch(None,root/'parser_smoke'/variant)
            search.grep_retriever.rga_cache=root/'parser_smoke_cache'/variant
            paths=await search.keywords(['UN Principles for Responsible Investment'])
            rows.append(dict(group=variant,files=paths,legacy_found=any(p.endswith('.doc') for p in paths)))
    finally:
        GrepRetriever._run_rga_async=staticmethod(original)
    passed=not rows[0]['legacy_found'] and rows[1]['legacy_found']
    save(root/'parser_correction_smoke.json',dict(passed=passed,rows=rows,
         purpose='Exercise the actual asynchronous keyword tool with a source-verified phrase; not a new benchmark question.'))
    assert passed, 'The real keyword tool did not distinguish the parser variants'
    print(json.dumps(dict(smoke_passed=passed)),flush=True)


async def main(root):
    assert (root/'support_complete.json').exists(), 'Finish the current source-check stage before timed replay'
    assert json.loads((root/'parser_correction_smoke.json').read_text())['passed']
    archive=root/'parser_initial_invalid'
    if not archive.exists():
        archive.mkdir()
        (archive/'runs').mkdir()
        for group in ['P0','P']:
            (root/'runs'/group).rename(archive/'runs'/group)
        for name in ['parser_validation.json','parser_progress.jsonl','parser_complete.json']:
            (root/name).rename(archive/name)
        save(archive/'classification.json',dict(valid_parser_comparison=False,
             reason='Only the unused synchronous executor was patched; live retrieval uses _run_rga_async. Both arms used the default parser.'))
    original=install(root,'corrected_replay')
    try:
        await parser_replay.main(root)
    finally:
        GrepRetriever._run_rga_async=staticmethod(original)
    complete=json.loads((root/'parser_complete.json').read_text())
    complete.update(corrected_async_hook=True,file_order='path in both arms',
                    driver_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    save(root/'parser_complete.json',complete)


if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('action',choices=['smoke','run'])
    p.add_argument('--root',type=Path,default=Path('/retrieval_followup_20261023'))
    args=p.parse_args()
    asyncio.run(smoke(args.root) if args.action=='smoke' else main(args.root))
