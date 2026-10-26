"""Adapt the existing audited scoring helpers for a fresh two-arm batch."""
from pathlib import Path
import shutil

HERE=Path(__file__).resolve().parent

def main():
    prior=HERE.parent/'rerank_top5_top10'
    source=(prior/'prepare_reviews.py').read_text(encoding='utf-8')
    source=source.replace("[parent/'support_reviews', parent/'followup120/support_reviews']",
        "[parent/'support_reviews', parent/'followup120/support_reviews', parent/'rerank_top5_top10/support_reviews']")
    source=source.replace("['Baseline','RR5','RR10']","['Baseline','RR10']")
    source=source.replace("    standards = {s['id']: s for s in read(standards_path)}",
        "    import subprocess\n    committed = subprocess.check_output(['git','show',read(HERE/'freeze.json')['source_commit']+':retrieval/inputs/standards.json'],cwd=parent.parent)\n    assert hashlib.sha256(committed).hexdigest()==sha(standards_path), 'Scoring standards changed since batch preparation'\n    standards = {s['id']: s for s in read(standards_path)}")
    (HERE/'prepare_reviews.py').write_text(source,encoding='utf-8')
    source=(prior/'analyze.py').read_text(encoding='utf-8')
    source=source.replace("['Baseline','RR5','RR10']","['Baseline','RR10']")
    source=source.replace("[('Baseline','RR5'),('Baseline','RR10'),('RR5','RR10')]","[('Baseline','RR10')]")
    source=source.replace("rerank_seconds=r.get('elapsed_s',0) if group!='Baseline' else ''",
        "stage_seconds=r.get('total_attempt_seconds',r.get('elapsed_s',0))")
    source=source.replace("cr=calls(HERE/'runs'/group) if group!='Baseline' else []","cr=calls(HERE/'runs'/group)")
    source=source.replace("task_latency=latency([r['elapsed_s'] for r in records.values() if r.get('candidate_count',0)>1]) if group!='Baseline' else None",
        "task_latency=latency([r.get('total_attempt_seconds',r['elapsed_s']) for r in records.values()])")
    source=source.replace("pc=[json.loads(line) for line in (HERE/'preflight_calls.jsonl').read_text(encoding='utf-8').splitlines()]",
        "pc=[json.loads(line) for p in [HERE/'preflight_calls.jsonl',HERE/'results/basic120/preflight_calls.jsonl'] for line in p.read_text(encoding='utf-8').splitlines()]")
    (HERE/'analyze.py').write_text(source,encoding='utf-8')
    for name in ['test_common.py','test_metrics.py']:
        shutil.copyfile(prior/name,HERE/name)
    print('Prepared paired scoring; prior source decisions include the previous completed reranking batch')

if __name__=='__main__': main()
