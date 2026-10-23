"""Read-only source validation and local parser/cache preflight; no LLM calls."""
import hashlib
import json
import subprocess
from pathlib import Path

from runtime_config import search_model

ROOT = Path(__file__).resolve().parents[1]
CONTAINER_SCRIPT = r'''
import asyncio, hashlib, importlib.metadata, inspect, json, os, subprocess, time
from pathlib import Path
from sirchmunk.learnings.knowledge_base import fast_extract
from sirchmunk.search import AgenticSearch

async def main():
    records=[]
    for p in sorted(Path('/mnt/docs/S').iterdir()):
        if not p.is_file(): continue
        rec={'file':p.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}
        started=time.time()
        try:
            extracted=await asyncio.wait_for(fast_extract(str(p)), timeout=60)
            content=extracted.content or ''
            rec.update(extracted_chars=len(content),control_characters=sum(ord(c)<32 and c not in '\n\r\t' for c in content),
                       extraction_ok=bool(content.strip()), extracted_sha256=hashlib.sha256(content.encode()).hexdigest())
        except Exception as e:
            rec.update(extraction_ok=False,extraction_error=f'{type(e).__name__}: {e}')
        try:
            proc=subprocess.run(['rga','--no-config','--rga-cache-max-blob-len=10000000',
                '--rga-cache-path=/poc_cache/rga_S','-m','1','[A-Za-z]',str(p)],capture_output=True,timeout=60)
            output=proc.stdout.decode('utf-8',errors='replace')
            rec.update(rga_exit_code=proc.returncode,rga_has_text=bool(output.strip()) and 'binary file matches' not in output.lower(),
                       rga_stderr=proc.stderr.decode('utf-8',errors='replace')[:1000])
        except Exception as e:
            rec.update(rga_has_text=False,rga_error=f'{type(e).__name__}: {e}')
        rec['elapsed_s']=round(time.time()-started,2)
        records.append(rec)
        print(json.dumps({'progress':len(records),'file':p.name,'extraction_ok':rec.get('extraction_ok'),'rga_has_text':rec.get('rga_has_text')}),flush=True)
    metadata={'model':os.getenv('LLM_MODEL_NAME'),'api_key_present':bool(os.getenv('LLM_API_KEY')),
       'version':importlib.metadata.version('sirchmunk'),'search_source_sha256':hashlib.sha256(Path(inspect.getfile(AgenticSearch)).read_bytes()).hexdigest(),
       'embedding_model':os.getenv('EMBEDDING_MODEL_ID'),'embedding_cache':os.getenv('EMBEDDING_CACHE_DIR'),
       'files':records}
    print('PREFLIGHT_RESULT='+json.dumps(metadata,ensure_ascii=False),flush=True)
asyncio.run(main())
'''


def run(output):
    output.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(['docker','exec','-i','-e',f'LLM_MODEL_NAME={search_model()}',
                           'sirchmunk','python','-'], input=CONTAINER_SCRIPT,
                          capture_output=True,text=True,encoding='utf-8',errors='replace')
    (output/'preflight.log').write_text(proc.stdout+'\n'+proc.stderr,encoding='utf-8')
    if proc.returncode:
        raise RuntimeError('Container preflight failed; see preflight.log')
    result=json.loads(next(line[len('PREFLIGHT_RESULT='):] for line in proc.stdout.splitlines() if line.startswith('PREFLIGHT_RESULT=')))
    inventory=json.loads((ROOT/'poc/questions/verification/audit_20261014/source_inventory.json').read_text(encoding='utf-8'))
    expected={r['file']:r['sha256'] for r in inventory}
    actual={r['file']:r['sha256'] for r in result['files']}
    result['corpus_hashes_match_audit']=actual==expected
    result['host_hashes_match_audit']=all(hashlib.sha256((ROOT/'poc_docs/S'/k).read_bytes()).hexdigest()==v for k,v in expected.items())
    result['parser_limitations']=[r['file'] for r in result['files'] if not r.get('extraction_ok') or not r.get('rga_has_text') or r.get('control_characters',0)>10]
    result['no_llm_calls']=True
    (output/'preflight.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    if not result['corpus_hashes_match_audit'] or not result['host_hashes_match_audit'] or not result['api_key_present']:
        raise RuntimeError('Corpus mismatch or missing model credential; see preflight.json')
    return result


if __name__=='__main__':
    import sys
    r=run(Path(sys.argv[1]))
    print(json.dumps({k:v for k,v in r.items() if k!='files'},ensure_ascii=False,indent=2))
