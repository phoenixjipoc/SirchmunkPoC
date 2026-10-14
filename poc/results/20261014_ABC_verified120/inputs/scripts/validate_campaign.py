"""Validate complete exported campaign records without making model requests."""
import argparse
import csv
import hashlib
import json
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def csv_rows(path):
    with path.open(encoding='utf-8-sig',newline='') as f:
        return list(csv.DictReader(f))


def jsonl(path):
    return [json.loads(s) for s in path.read_text(encoding='utf-8').split('\n') if s.strip()]


def validate(root):
    manifest=json.loads((root/'campaign.json').read_text(encoding='utf-8'))
    status=json.loads((root/'export_status.json').read_text(encoding='utf-8'))
    assert manifest['state']=='complete', 'Search/judging campaign incomplete'
    assert status['export_complete'] and not status['pending_reviews'], 'Reviews incomplete'
    reference=csv_rows(root/'inputs/questions.csv')
    expected=[r['id'] for r in reference]
    assert len(expected)==len(set(expected))==120
    assert digest(root/'inputs/questions.csv')==manifest['question_sha256']
    inventory=json.loads((root/'inputs/source_inventory.json').read_text(encoding='utf-8'))
    corpus=Path(__file__).resolve().parent.parent/'poc_docs/S'
    assert len(inventory)==81
    assert {p.name for p in corpus.iterdir() if p.is_file()}=={r['file'] for r in inventory}
    assert all(digest(corpus/r['file'])==r['sha256'] for r in inventory), 'Raw corpus changed'
    all_rows=csv_rows(root/'all_results.csv')
    assert len(all_rows)==360
    totals={r['stage']:r for r in csv_rows(root/'summary.csv') if r['group']=='ALL'}
    checks=[]
    work_paths=set()
    image_ids=set()
    labels={'correct','correct_refusal','partial','wrong','hallucinated','no_answer','error'}
    for stage in ('A','B','C'):
        directory=root/stage
        meta=json.loads((directory/'run_meta.json').read_text(encoding='utf-8'))
        config=manifest['configs'][stage]
        assert meta['state']=='complete' and meta['mode']=='DEEP'
        assert meta['n_questions']==120 and meta['n_files']==81
        assert meta['model']==manifest['model'] and meta['top_k_files']==config['top_k']
        assert meta['cluster_reuse']==config['reuse']
        assert float(meta['cluster_sim_threshold'])==.85
        assert meta['questions_sha256']==digest(directory/'question_snapshot.csv')==manifest['question_sha256']
        assert meta['runner_sha256']==manifest['scripts']['harness/sirch_runner.py']
        assert meta['rga_cache']==manifest['rga_cache'].split(',')[0].replace('shared ','')
        work_paths.add(meta['work_path']);image_ids.add(meta['image_id'])
        raw=jsonl(directory/'results.jsonl')
        search_input=jsonl(directory/'questions.jsonl')
        assert [r['id'] for r in search_input]==expected
        assert all(set(r)=={'id','question'} for r in search_input), 'Reference leaked into search input'
        assert all(r['question']==q['question'] for r,q in zip(search_input,reference))
        judged=csv_rows(directory/'results_judged.csv')
        final=[r for r in all_rows if r['stage']==stage]
        assert [r['id'] for r in raw]==[r['id'] for r in judged]==[r['id'] for r in final]==expected
        assert all(r['question']==q['question'] for r,q in zip(raw,reference))
        assert all(r['model']==manifest['model'] for r in raw)
        assert all(r['answer']==f['answer'] and int(r['total_tokens'])==int(f['total_tokens'])
                   for r,f in zip(raw,final)), 'Raw answer/usage changed during export'
        assert all(r['final_label'] in labels for r in final)
        assert all(float(r['latency_s'])>=0 and int(r['total_tokens'] or 0)>=0 for r in final)
        if not config['reuse']:assert not any(r.get('reused_cluster_id') for r in raw)
        clusters=csv_rows(directory/'clusters.csv')
        full=jsonl(directory/'clusters_full.jsonl')
        assert len(clusters)==len(full)==manifest['stages'][stage]['clusters_exported']
        assert len({r['id'] for r in clusters})==len(clusters)
        counts=Counter(r['final_label'] for r in final)
        assert sum(counts.values())==120 and int(totals[stage]['n'])==120
        assert all(int(totals[stage][label])==counts[label] for label in labels)
        assert float(totals[stage]['overall_correct_pct'])==round(100*(counts['correct']+counts['correct_refusal'])/120,2)
        assert int(totals[stage]['total_tokens'])==sum(int(r['total_tokens'] or 0) for r in final)
        checks.append({'stage':stage,'questions':120,'clusters':len(clusters),'labels':dict(counts),
                       'search_tokens':sum(int(r['total_tokens'] or 0) for r in final),
                       'reuse_hits':sum(bool(r.get('reused_cluster_id')) for r in raw)})
    assert len(work_paths)==3 and len(image_ids)==1
    assert len(csv_rows(root/'question_comparison.csv'))==120
    assert len(csv_rows(root/'paired_results.csv'))==45
    assert all(r['review_status']=='reviewed' for r in csv_rows(root/'review_queue.csv'))
    result={'validated_at':datetime.now(timezone(timedelta(hours=8))).isoformat(timespec='seconds'),
            'passed':True,'records':360,'raw_corpus_files':81,'raw_corpus_hashes_unchanged':True,
            'independent_work_paths':True,'same_image_model_questions':True,'stages':checks,
            'search_input_contains_only_id_and_question':True,'answers_and_usage_preserved':True,
            'note':'Structural/data-integrity checks; does not prove all semantic grades are correct.'}
    (root/'validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False))


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('campaign_dir',type=Path)
    validate(ap.parse_args().campaign_dir)
