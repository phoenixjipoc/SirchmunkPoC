"""Run one evaluation config against the local sirchmunk container.

Each run gets a fresh Sirchmunk work path inside the container, so knowledge
clusters start empty and don't leak between runs (no container restart needed).
Pass --work-path to reuse a previous run's clusters, e.g. for the Evolve
experiment.

Usage:
  python poc/run_eval.py --tier S                      # DEEP, all questions
  python poc/run_eval.py --tier S --ids CONS-01 OTH-03
  python poc/run_eval.py --tier S --types detail pair_a pair_b --limit 5

Output: poc/results/<run_id>/{run_meta.json, results.jsonl, results.csv, raw/*.json}
"""
import argparse
import csv
import hashlib
import json
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path, PurePosixPath

POC = Path(__file__).parent
CONTAINER = "sirchmunk"
RUNS_ROOT = "/poc_runs"  # inside the container
CN_TZ = timezone(timedelta(hours=8))


def now():
    return datetime.now(CN_TZ)


def docker(*args, check=True, capture=True):
    r = subprocess.run(["docker", *args], capture_output=capture, text=True,
                       encoding="utf-8", errors="replace")
    if check and r.returncode != 0:
        sys.exit(f"docker {' '.join(args)} failed:\n{r.stderr}")
    return r.stdout.strip() if capture else ""


def load_questions(path, ids=None, types=None, limit=None):
    with open(path, encoding="utf-8-sig") as f:
        qs = [r for r in csv.DictReader(f) if r.get("id")]
    if ids:
        qs = [q for q in qs if q["id"] in ids]
    if types:
        qs = [q for q in qs if q["type"] in types]
    return qs[:limit] if limit else qs


def gold_files(q):
    return {s.strip() for s in (q.get("gold_source_file") or "").split(";") if s.strip()}


def basenames(paths):
    return [PurePosixPath(p).name for p in paths]


def score_retrieval(q, rec):
    """Retrieval flags relative to the gold source file(s)."""
    gold = gold_files(q)
    cand = basenames(rec["candidate_files"])
    out = {"gold_in_candidates": "", "gold_rank_in_candidates": "",
           "gold_in_sampled": "", "gold_in_evidence": "",
           "gold_source_count": len(gold), "gold_coverage_candidates": "",
           "gold_coverage_sampled": "", "gold_coverage_evidence": "",
           "gold_coverage_found_evidence": "", "gold_coverage_cited": ""}
    if not gold:
        return out
    ranks = [cand.index(g) + 1 for g in gold if g in cand]
    out["gold_in_candidates"] = bool(ranks)
    out["gold_rank_in_candidates"] = min(ranks) if ranks else ""
    out["gold_in_sampled"] = bool(gold & set(basenames(rec["sampled_files"])))
    out["gold_in_evidence"] = bool(gold & set(basenames(rec["evidence_files"])))
    for metric, key in [('candidates', 'candidate_files'), ('sampled', 'sampled_files'),
                        ('evidence', 'evidence_files'), ('found_evidence', 'evidence_found_files'),
                        ('cited', 'cited_files')]:
        out['gold_coverage_' + metric] = round(len(gold & set(basenames(rec.get(key, [])))) / len(gold), 4)
    return out


CSV_COLS = ["id", "type", "pair_id", "question", "gold_source_file", "gold_answer",
            "answer", "no_result", "gate_should_answer",
            "gold_in_candidates", "gold_rank_in_candidates", "gold_in_sampled", "gold_in_evidence",
            "n_candidates", "rga_timeout", "evidence_files", "reused_cluster",
            "latency_s", "llm_calls", "total_tokens", "prompt_tokens", "completion_tokens",
            "error", "pre_gate_answer", "gold_source_count", "gold_coverage_candidates",
            "gold_coverage_sampled", "gold_coverage_evidence", "gold_coverage_found_evidence",
            "gold_coverage_cited", "cited_files", "cited_found_files", "reused_cluster_id",
            "cluster_id", "llm_failed_calls", "serialization_error"]


def write_csv(questions, results_jsonl, out_csv):
    by_id = {q["id"]: q for q in questions}
    rows = []
    for line in open(results_jsonl, encoding="utf-8"):
        rec = json.loads(line)
        q = by_id.get(rec["id"], {})
        rows.append({
            **{k: q.get(k, "") for k in ("id", "type", "pair_id", "gold_source_file", "gold_answer")},
            **{k: rec.get(k) for k in ("question", "answer", "no_result", "gate_should_answer",
                                       "reused_cluster", "latency_s", "llm_calls", "total_tokens",
                                       "prompt_tokens", "completion_tokens", "error",
                                       "pre_gate_answer", "reused_cluster_id", "cluster_id",
                                       "llm_failed_calls", "serialization_error")},
            "id": rec["id"],
            "n_candidates": len(rec["candidate_files"]),
            "rga_timeout": any("timed out" in w for w in rec.get("warnings", [])),
            "evidence_files": ";".join(dict.fromkeys(basenames(rec["evidence_files"]))),
            "cited_files": ";".join(dict.fromkeys(basenames(rec.get('cited_files', [])))),
            "cited_found_files": ";".join(dict.fromkeys(basenames(rec.get('cited_found_files', [])))),
            **score_retrieval(q, rec),
        })
    with open(out_csv, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=CSV_COLS)
        w.writeheader()
        w.writerows(rows)
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tier", required=True, help="Corpus tier folder under /mnt/docs (S, M, L)")
    ap.add_argument("--mode", default="DEEP", choices=["DEEP", "FAST"])
    ap.add_argument("--questions", default=str(POC / "questions" / "questions.csv"))
    ap.add_argument("--ids", nargs="*")
    ap.add_argument("--types", nargs="*")
    ap.add_argument("--limit", type=int)
    ap.add_argument("--top-k-files", type=int)
    ap.add_argument("--tag", default="", help="Free-text suffix for the run id")
    ap.add_argument("--run-id", help="Explicit unique run identifier")
    ap.add_argument("--output-dir", type=Path, help="Local directory for this run")
    ap.add_argument("--work-path", help="Container work path to reuse (keeps clusters)")
    ap.add_argument("--resume", help="Existing run_id to continue (skips finished questions)")
    ap.add_argument("--no-reuse", action="store_true",
                    help="Disable knowledge cluster reuse (SIRCHMUNK_ENABLE_CLUSTER_REUSE=false)")
    ap.add_argument("--sim-threshold", type=float,
                    help="Override CLUSTER_SIM_THRESHOLD (default 0.85)")
    ap.add_argument("--cold-rga", action="store_true",
                    help="Don't use the shared per-tier rga text cache (every file is re-extracted)")
    args = ap.parse_args()

    questions = load_questions(args.questions, args.ids, args.types, args.limit)
    if not questions:
        sys.exit("No questions selected.")

    run_id = args.resume or args.run_id or "_".join(filter(None, [
        now().strftime("%Y%m%d-%H%M%S"), args.tier, args.mode, args.tag]))
    c_dir = f"{RUNS_ROOT}/{run_id}"
    local_dir = args.output_dir or POC / "results" / run_id
    if local_dir.exists() and (local_dir / 'run_meta.json').exists() and not args.resume:
        sys.exit('Run already exists; use --resume explicitly.')
    local_dir.mkdir(parents=True, exist_ok=True)
    snapshot = local_dir / 'question_snapshot.csv'
    questions_hash = hashlib.sha256(Path(args.questions).read_bytes()).hexdigest()
    if snapshot.exists() and hashlib.sha256(snapshot.read_bytes()).hexdigest() != questions_hash:
        sys.exit('Question snapshot changed; cannot resume this run.')
    shutil.copyfile(args.questions, snapshot)

    # Stage runner + questions in the container.
    qjsonl = local_dir / "questions.jsonl"
    with open(qjsonl, "w", encoding="utf-8") as f:
        for q in questions:
            f.write(json.dumps({"id": q["id"], "question": q["question"]}, ensure_ascii=False) + "\n")
    docker("exec", CONTAINER, "mkdir", "-p", c_dir)
    docker("cp", str(POC / "harness" / "sirch_runner.py"), f"{CONTAINER}:{c_dir}/sirch_runner.py")
    docker("cp", str(qjsonl), f"{CONTAINER}:{c_dir}/questions.jsonl")

    n_files = docker("exec", CONTAINER, "sh", "-c", f"ls /mnt/docs/{args.tier} | wc -l")
    meta = {
        "run_id": run_id, "tier": args.tier, "mode": args.mode, "n_files": int(n_files),
        "n_questions": len(questions), "top_k_files": args.top_k_files,
        "work_path": args.work_path or f"{c_dir}/work",
        "image": docker("inspect", "-f", "{{.Config.Image}}", CONTAINER),
        "image_id": docker("inspect", "-f", "{{.Image}}", CONTAINER),
        "model": docker("exec", CONTAINER, "sh", "-c", "echo $LLM_MODEL_NAME"),
        "cluster_sim_threshold": docker("exec", CONTAINER, "sh", "-c",
                                        "echo ${CLUSTER_SIM_THRESHOLD:-0.85}"),
        "started": now().isoformat(timespec="seconds"),
        "questions_sha256": questions_hash,
        "runner_sha256": hashlib.sha256((POC / 'harness' / 'sirch_runner.py').read_bytes()).hexdigest(),
        "question_timeout_s": 600, "state": "running",
        "usage_accounting": "successful llm.achat response usage; logical calls include failures, internal retries may add HTTP attempts",
    }
    print(json.dumps(meta, indent=1))

    env = ['-e', f'SIRCHMUNK_ENABLE_CLUSTER_REUSE={str(not args.no_reuse).lower()}']
    if args.sim_threshold is not None:
        env += ["-e", f"CLUSTER_SIM_THRESHOLD={args.sim_threshold}"]
    meta["cluster_reuse"] = not args.no_reuse
    if args.sim_threshold is not None:
        meta["cluster_sim_threshold"] = str(args.sim_threshold)

    cmd = ["exec", *env, CONTAINER, "python", "-u", f"{c_dir}/sirch_runner.py",
           "--questions", f"{c_dir}/questions.jsonl", "--out-dir", c_dir,
           "--paths", f"/mnt/docs/{args.tier}", "--mode", args.mode]
    if args.work_path:
        cmd += ["--work-path", args.work_path]
    if args.top_k_files:
        cmd += ["--top-k-files", str(args.top_k_files)]
    if not args.cold_rga:
        cmd += ["--rga-cache", f"/poc_cache/rga_{args.tier}"]
    meta['rga_cache'] = None if args.cold_rga else f'/poc_cache/rga_{args.tier}'
    meta['command'] = ['docker', *cmd]
    meta_path = local_dir / 'run_meta.json'
    meta_path.write_text(json.dumps(meta, indent=2), encoding='utf-8')

    t0 = time.time()
    with (local_dir / 'execution.log').open('a', encoding='utf-8') as log:
        proc = subprocess.Popen(['docker', *cmd], stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                text=True, encoding='utf-8', errors='replace', bufsize=1)
        for line in proc.stdout:
            log.write(line)
            log.flush()
            # Keep the terminal concise; the complete engine log is in the file.
            if line.startswith('[') and ('/120]' in line or '[warmup]' in line):
                print(line, end='', flush=True)
        proc.wait()
    meta["wall_clock_s"] = round(time.time() - t0, 1)
    meta["finished"] = now().isoformat(timespec="seconds")
    meta["runner_exit_code"] = proc.returncode

    # Copy results back (also on failure, to keep partial output).
    docker("cp", f"{CONTAINER}:{c_dir}/raw", str(local_dir), check=False)
    docker("cp", f"{CONTAINER}:{c_dir}/results.jsonl", str(local_dir / "results.jsonl"), check=False)
    warm = docker("exec", CONTAINER, "cat", f"{c_dir}/warmup.json", check=False)
    if warm:
        meta["warmup"] = json.loads(warm)
    (local_dir / "run_meta.json").write_text(json.dumps(meta, indent=1), encoding="utf-8")

    results_jsonl = local_dir / "results.jsonl"
    if not results_jsonl.exists():
        sys.exit(f"No results produced. See container output above. Run dir: {local_dir}")
    rows = write_csv(questions, results_jsonl, local_dir / "results.csv")
    meta['completed_questions'] = len(rows)
    meta['state'] = 'complete' if proc.returncode == 0 and len(rows) == len(questions) else 'incomplete'
    meta_path.write_text(json.dumps(meta, indent=2), encoding='utf-8')

    answered = sum(not r["error"] and bool(r['answer']) and not r["no_result"] for r in rows)
    lat = sorted(r["latency_s"] for r in rows)
    print(f"\nRun {run_id}: {len(rows)} questions, {answered} answered; "
          f"median latency {lat[len(lat) // 2] if lat else 0:.1f}s")
    print(f"Results: {local_dir / 'results.csv'}")
    if meta['state'] != 'complete':
        sys.exit(1)


if __name__ == "__main__":
    main()
