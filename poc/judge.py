"""LLM-as-judge for one run: adds judge labels to results.csv -> results_judged.csv.

Labels for answer rows:
  correct | partial | wrong        normal questions
  no_answer                        system returned "No results found." (no LLM call)
  correct_refusal | hallucinated   unanswerable questions

pre_gate_label grades the answer the summary gate blocked. It shows how often
a "no result" hid a usable answer.

The judge uses any OpenAI-compatible endpoint. By default it reads the model
from the run metadata and credentials from the sirchmunk container env, so the
judge uses the search model unless --model is given.

Usage: python poc/judge.py poc/results/<run_id> [--model MODEL] [--base-url ...]
"""
import argparse
import csv
import json
import hashlib
import os
import re
import subprocess
import sys
import time
from pathlib import Path

import requests
import truststore

truststore.inject_into_ssl()

PROMPT = """You are grading a document Q&A system against a gold answer.

Question: {question}
Question type: {qtype}
Gold answer: {gold_answer}
Gold supporting passage: {gold_passage}
Acceptance criteria from the independent source audit: {acceptance_notes}

System answer:
<<<
{answer}
>>>

Grade the system answer:
- "correct": contains the key facts of the gold answer and nothing that contradicts it. Extra correct detail is fine.
- "partial": some REQUIRED key facts are right, but required parts are missing. Optional examples are not required. Respect qualifications and source inconsistencies in the acceptance criteria.
- "wrong": the key fact is wrong or comes from a different document (e.g. another fund's RFP), or the answer says the information is not available when the gold shows it is.
If the gold answer is "NOT IN CORPUS", grade "correct_refusal" if the system says it cannot find or confirm the answer, and "hallucinated" if it gives a specific answer.

Return JSON only: {{"label": "...", "reason": "<one sentence>"}}"""


def container_env(name):
    r = subprocess.run(["docker", "exec", "sirchmunk", "printenv", name],
                       capture_output=True, text=True)
    return r.stdout.strip()


def judge(session, cfg, q, answer):
    prompt = PROMPT.format(question=q["question"], qtype=q["type"],
                           gold_answer=q["gold_answer"], gold_passage=q["gold_passage"],
                           acceptance_notes=q.get('verify_note', '').split(' | Acceptance: ')[-1]
                           if ' | Acceptance: ' in q.get('verify_note', '') else '',
                           answer=answer)
    for attempt in range(4):
        r = None
        try:
            r = session.post(f"{cfg['base_url']}/chat/completions", timeout=180, json={
                "model": cfg["model"],
                "messages": [{"role": "user", "content": prompt}],
                "response_format": {"type": "json_object"},
            })
            r.raise_for_status()
            break
        except requests.RequestException:
            if attempt == 3 or (r is not None and r.status_code in (400, 401, 403)):
                raise
            time.sleep(2 ** attempt)
    text = r.json()["choices"][0]["message"]["content"]
    m = re.search(r"\{.*\}", text, re.S)
    out = json.loads(m.group(0) if m else text)
    label = out.get('label', '').strip().lower()
    allowed = {'correct_refusal', 'hallucinated'} if q['type'] == 'unanswerable' else {'correct', 'partial', 'wrong'}
    if label not in allowed:
        raise ValueError(f'Unexpected judge label: {label}')
    return label, out.get("reason", ""), r.json().get('usage', {})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir")
    ap.add_argument("--questions", help="Defaults to the immutable run snapshot")
    ap.add_argument("--model")
    ap.add_argument("--base-url")
    ap.add_argument("--api-key-env", default="", help="Host env var holding the judge API key")
    args = ap.parse_args()

    run_dir = Path(args.run_dir)
    run_model = json.loads((run_dir / "run_meta.json").read_text(encoding="utf-8"))["model"]
    cfg = {
        "model": args.model or run_model,
        "base_url": (args.base_url or container_env("LLM_BASE_URL")).rstrip("/"),
    }
    key = os.getenv(args.api_key_env) if args.api_key_env else container_env("LLM_API_KEY")
    if not key:
        sys.exit("No judge API key.")
    session = requests.Session()
    session.headers["Authorization"] = f"Bearer {key}"

    questions_path = Path(args.questions) if args.questions else run_dir / 'question_snapshot.csv'
    if not questions_path.exists():
        sys.exit('No frozen question snapshot; specify --questions explicitly for historical runs.')
    gold = {q["id"]: q for q in csv.DictReader(open(questions_path, encoding="utf-8-sig"))}
    rows = list(csv.DictReader(open(run_dir / "results.csv", encoding="utf-8-sig")))
    checkpoint = run_dir / 'judge_records.jsonl'
    previous = {r['id']: r for r in (json.loads(s) for s in checkpoint.read_text(encoding='utf-8').splitlines())} if checkpoint.exists() else {}
    usage_records = []

    for i, row in enumerate(rows, 1):
        q = {**gold[row["id"]], "question": row["question"]}
        if row['question'] != gold[row['id']]['question']:
            raise ValueError('Run question differs from frozen reference: ' + row['id'])
        fingerprint = hashlib.sha256(json.dumps({'row':row,'q':q,'cfg':cfg,'prompt':PROMPT},sort_keys=True).encode()).hexdigest()
        saved = previous.get(row['id'])
        if saved:
            if saved['fingerprint'] != fingerprint:
                raise ValueError('Judge inputs changed on resume: ' + row['id'])
            row.update(saved['judgment'])
            usage_records.extend(saved.get('usages', []))
            continue
        unanswerable = q["type"] == "unanswerable"
        usages = []
        if row.get('error') or not (row.get('answer') or '').strip():
            row['judge_label'] = 'error'
            row['judge_reason'] = row.get('error') or 'Empty answer without explicit refusal.'
        elif row["no_result"] == "True":
            row["judge_label"] = "correct_refusal" if unanswerable else "no_answer"
            row["judge_reason"] = "System returned no result."
        else:
            row["judge_label"], row["judge_reason"], usage = judge(session, cfg, q, row["answer"])
            usages.append(usage)
        row["pre_gate_label"] = ""
        if row["judge_label"] != 'error' and row["no_result"] == "True" and row.get("pre_gate_answer"):
            row["pre_gate_label"], _, usage = judge(session, cfg, q, row["pre_gate_answer"])
            usages.append(usage)
        judgment = {k:row[k] for k in ('judge_label','judge_reason','pre_gate_label')}
        with checkpoint.open('a', encoding='utf-8') as f:
            f.write(json.dumps({'id':row['id'],'fingerprint':fingerprint,'judgment':judgment,'usages':usages},ensure_ascii=False)+'\n')
        usage_records.extend(usages)
        print(f"[{i}/{len(rows)}] {row['id']} {row['judge_label']} {row['pre_gate_label']}", flush=True)

    cols = list(rows[0].keys())
    with open(run_dir / "results_judged.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    meta_path = run_dir / "run_meta.json"
    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    meta["judge"] = cfg
    meta['judge']['same_model_as_search'] = cfg['model'] == meta.get('model')
    meta['judge']['llm_calls'] = len(usage_records)
    meta['judge']['total_tokens'] = sum(u.get('total_tokens',0) for u in usage_records)
    meta['judge']['questions_sha256'] = hashlib.sha256(questions_path.read_bytes()).hexdigest()
    meta['judge']['prompt_sha256'] = hashlib.sha256(PROMPT.encode()).hexdigest()
    meta_path.write_text(json.dumps(meta, indent=1), encoding="utf-8")
    print(f"-> {run_dir / 'results_judged.csv'}")


if __name__ == "__main__":
    main()
