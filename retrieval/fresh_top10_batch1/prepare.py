"""Create a fresh retrieval-and-reranking batch, without historical candidates."""
import json
import shutil
import subprocess
from pathlib import Path

HERE=Path(__file__).resolve().parent

def main():
    if (HERE/'freeze.json').exists(): raise RuntimeError('Batch already frozen')
    parent=HERE.parent
    for name in ['inputs','adapter','execution_logs']: (HERE/name).mkdir(parents=True,exist_ok=True)
    for name in ['queries.json','corpus.json']:
        shutil.copyfile(parent/'inputs'/name,HERE/'inputs'/name)
    shutil.copyfile(parent/'rerank_top5_top10/common.py',HERE/'common.py')
    from common import read,save,sha
    for name in ['basic_run.py','runtime.py']:
        shutil.copyfile(parent/'followup120/adapter'/name,HERE/'adapter'/name)
    shutil.copyfile(parent/'review_support.py',HERE/'adapter/review_support.py')
    shutil.copyfile(parent/'rerank_top5_top10/prompt.txt',HERE/'prompt.txt')
    # These modules are unchanged helpers. Only the fresh batch driver is executed.
    shutil.copyfile(parent/'rerank_top5_top10/run.py',HERE/'rank_adapter.py')
    shutil.copyfile(parent/'rerank_top5_top10/check_support.py',HERE/'check_support.py')
    config=read(parent/'inputs/config.json')
    config['container_root']='/retrieval_fresh_top10_batch1_20261026'
    save(HERE/'inputs/config.json',config)
    save(HERE/'inputs/source_hashes.json',read(parent/'results/basic120/preflight.json')['source_hashes'])
    settings=read(parent/'rerank_top5_top10/settings.json')
    settings.update(groups={'RR10':10},interleave_groups=False,comparison_groups=['Baseline','RR10'],
        baseline='Fresh native retrieval within this batch',parsing_cache='New isolated cache',directory_candidates=20)
    save(HERE/'settings.json',settings)
    assert not (HERE/'baseline').exists() and not (HERE/'runs').exists()
    files=[*list((HERE/'inputs').glob('*.json')),*list((HERE/'adapter').glob('*.py')),
        *[HERE/n for n in ['prepare.py','common.py','run_batch.py','rank_adapter.py','check_support.py','settings.json','prompt.txt','PLAN.md']]]
    save(HERE/'freeze.json',dict(source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=parent.parent,text=True).strip(),
        files={p.relative_to(HERE).as_posix():sha(p) for p in sorted(files)},historical_results_imported=False))
    print('Frozen one batch: 120 fresh retrieval tasks, followed by 120 reranking tasks')

if __name__=='__main__': main()
