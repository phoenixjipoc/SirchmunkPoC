"""Replay identical keyword terms against raw files with/without a DOC adapter."""
import argparse
import asyncio
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent/'adapter'))
from basic_run import DocumentSearch,save
from runtime import append
from sirchmunk.retrieve.text_retriever import GrepRetriever


async def main(root):
    assert (root/'retrieval_complete.json').exists(), 'Keep parser replay separate from timed remote retrieval'
    config=root/'legacy_rga.json'
    save(config,{'custom_adapters':[dict(name='legacy_word97',version=1,
         description='Corpus-specific Word97 piece-table parser',extensions=['doc'],
         binary='python',args=[str(root/'legacy_adapter.py')],disabled_by_default=False)]})
    probes=[]
    for variant,flags in [('P0',[]),('P',[f'--rga-config-file={config}'])]:
        for path in sorted(Path('/mnt/docs/S').iterdir()):
            if not path.is_file(): continue
            cmd=['rga','--no-config',*flags,'--json',f'--rga-cache-path={root}/parser_cache/{variant}',
                 '--rga-cache-max-blob-len=10000000','-m','1','[A-Za-z]',str(path)]
            p=await asyncio.create_subprocess_exec(*cmd,stdout=asyncio.subprocess.PIPE,stderr=asyncio.subprocess.PIPE)
            stdout,stderr=await asyncio.wait_for(p.communicate(),90)
            events=[json.loads(line) for line in stdout.splitlines()]
            matches=[e['data']['lines'] for e in events if e.get('type')=='match']
            readable=any(isinstance(m.get('text'),str) and m['text'].isascii() for m in matches)
            # Non-ASCII punctuation is normal; byte-only lines are not readable text.
            readable=any(isinstance(m.get('text'),str) and len(m['text'].strip())>0 for m in matches)
            probes.append(dict(group=variant,file=path.name,returncode=p.returncode,readable_text=readable,
                               text_matches=sum('text' in m for m in matches),byte_matches=sum('bytes' in m for m in matches),
                               stderr=stderr.decode(errors='replace')[:1500]))
    save(root/'parser_validation.json',probes)
    original=GrepRetriever._run_rga
    questions=json.loads((root/'inputs/queries.json').read_text())
    started=time.monotonic()
    for i,q in enumerate(questions):
        old=json.loads((root/'baseline'/(q['id']+'.json')).read_text())
        for variant in ['P0','P']:
            output=root/'runs'/variant/'queries'/(q['id']+'.json')
            if output.exists(): continue
            if variant=='P':
                GrepRetriever._run_rga=staticmethod(lambda args,json_output=True: original(
                    [f'--rga-config-file={config}',*args],json_output=json_output))
            else: GrepRetriever._run_rga=staticmethod(original)
            search=DocumentSearch(None,root/'work'/variant)
            search.grep_retriever.rga_cache=root/'parser_cache'/variant
            start=time.monotonic()
            paths=await search.keywords(old['keyword_terms'])
            merged=search._merge_file_paths(paths,[],old['directory_files'])
            record=dict(query_id=q['id'],question=q['question'],type=q['type'],pair_id=q['pair_id'],group=variant,
                        keyword_files=paths,directory_files=old['directory_files'],merged_files=merged,
                        keyword_terms=old['keyword_terms'],keyword_logs=search.keyword_logs,
                        status='ok' if merged else 'empty_retrieval',evidence_sampling=False,answer_generated=False,cluster_used=False,
                        references=[dict(rank=i+1,file=Path(p).name,path=p) for i,p in enumerate(merged[:10])],
                        elapsed_s=round(time.monotonic()-start,3),calls=0,usage={})
            save(output,record)
        progress=dict(group='parser_replay',index=i+1,total=120,id=q['id'])
        append(root/'parser_progress.jsonl',progress); print(json.dumps(progress),flush=True)
    GrepRetriever._run_rga=staticmethod(original)
    save(root/'parser_complete.json',dict(questions=120,groups=['P0','P'],elapsed_s=round(time.monotonic()-started,3),
         adapter_sha256=hashlib.sha256((root/'legacy_adapter.py').read_bytes()).hexdigest(),
         config_sha256=hashlib.sha256(config.read_bytes()).hexdigest()))


if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--root',type=Path,default=Path('/retrieval_followup_20261023'))
    asyncio.run(main(p.parse_args().root))
