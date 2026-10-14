"""Export knowledge clusters from the sirchmunk container to CSV on the host.

Each eval run keeps its clusters in the container at
/poc_runs/<run_id>/work/.cache/knowledge/knowledge_clusters.parquet.
This script reads them with duckdb inside the container and writes
poc/results/<run_id>/clusters.csv. Evidence text is left out of the CSV
(it is whole documents); --full also writes clusters_full.jsonl with it.

Usage:
  python poc/export_clusters.py                    # every run under /poc_runs
  python poc/export_clusters.py <run_id> ... [--api] [--full]
"""
import argparse
import csv
import json
import subprocess
import sys
from pathlib import Path

POC = Path(__file__).parent
CONTAINER = "sirchmunk"
RUNS_ROOT = "/poc_runs"  # inside the container
API_KNOWLEDGE = "/data/sirchmunk/.cache/knowledge/knowledge_clusters.parquet"
MAX_CELL = 30000  # Excel cell limit is 32,767 chars

# Runs inside the container: argv[1] = parquet path, argv[2] = "1" to include evidence text.
READER = r'''
import duckdb, json, sys, posixpath
path, full = sys.argv[1], sys.argv[2] == "1"

def load(v):
    if v is None:
        return []
    try:
        return json.loads(v)
    except Exception:
        return [v]

cur = duckdb.connect().execute(f"select * from read_parquet('{path}')")
cols = [d[0] for d in cur.description]
for row in cur.fetchall():
    r = dict(zip(cols, row))
    evs = load(r.get("evidences"))
    files = list(dict.fromkeys(posixpath.basename(str(e.get("file_or_url", ""))) for e in evs if isinstance(e, dict)))
    desc = load(r.get("description"))
    out = {
        "id": r.get("id"),
        "name": r.get("name"),
        "description": "\n".join(map(str, desc)) if isinstance(desc, list) else str(desc),
        "content": r.get("content"),
        "queries": load(r.get("queries")),
        "hotness": r.get("hotness"),
        "confidence": r.get("confidence"),
        "version": r.get("version"),
        "create_time": str(r.get("create_time")),
        "last_modified": str(r.get("last_modified")),
        "evidence_files": files,
        "n_evidences": len(evs),
        "evidence_chars": sum(len(str(e.get("summary", ""))) for e in evs if isinstance(e, dict)),
        "search_results_top5": [posixpath.basename(str(p)) for p in load(r.get("search_results"))[:5]],
        "has_embedding": r.get("embedding_vector") is not None,
    }
    if full:
        out["evidences"] = evs
    print(json.dumps(out, ensure_ascii=False, default=str))
'''

CSV_COLS = ["id", "name", "question_ids", "queries", "n_queries", "hotness", "confidence",
            "version", "create_time", "last_modified", "evidence_files", "n_evidences",
            "evidence_chars", "search_results_top5", "has_embedding", "description", "content"]


def docker(*args, input=None):
    r = subprocess.run(["docker", *args], capture_output=True, input=input,
                       text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        sys.exit(f"docker {' '.join(args[:3])} failed:\n{r.stderr}")
    return r.stdout


def list_runs():
    out = docker("exec", CONTAINER, "sh", "-c",
                 f"ls -d {RUNS_ROOT}/*/work/.cache/knowledge/knowledge_clusters.parquet 2>/dev/null")
    return [p.split("/")[2] for p in out.split()]


def question_ids_by_text(run_dir):
    """Map question text -> id from the run's local results.jsonl."""
    path = run_dir / "results.jsonl"
    if not path.exists():
        return {}
    ids = {}
    for line in open(path, encoding="utf-8"):
        rec = json.loads(line)
        ids[rec["question"].strip()] = rec["id"]
    return ids


def export(parquet, out_dir, full):
    out = docker("exec", "-i", CONTAINER, "python", "-", parquet, "1" if full else "0", input=READER)
    clusters = [json.loads(line) for line in out.splitlines() if line.strip()]
    qids = question_ids_by_text(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    rows = []
    for c in clusters:
        rows.append({
            **{k: c.get(k) for k in CSV_COLS if k in c},
            "question_ids": ";".join(qids.get(q.strip(), "?") for q in c["queries"]),
            "queries": " || ".join(c["queries"]),
            "n_queries": len(c["queries"]),
            "evidence_files": ";".join(c["evidence_files"]),
            "search_results_top5": ";".join(c["search_results_top5"]),
            "description": (c["description"] or "")[:MAX_CELL],
            "content": (c["content"] or "")[:MAX_CELL],
        })
    rows.sort(key=lambda r: r["create_time"])
    with open(out_dir / "clusters.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=CSV_COLS)
        w.writeheader()
        w.writerows(rows)
    if full:
        with open(out_dir / "clusters_full.jsonl", "w", encoding="utf-8") as f:
            for c in clusters:
                f.write(json.dumps(c, ensure_ascii=False) + "\n")
    return len(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run_ids", nargs="*")
    ap.add_argument("--api", action="store_true", help="Also export the API's own clusters")
    ap.add_argument("--full", action="store_true", help="Also write clusters_full.jsonl with evidence text")
    args = ap.parse_args()

    targets = [(f"{RUNS_ROOT}/{r}/work/.cache/knowledge/knowledge_clusters.parquet",
                POC / "results" / r) for r in (args.run_ids or list_runs())]
    if args.api:
        targets.append((API_KNOWLEDGE, POC / "results" / "api_clusters"))
    if not targets:
        sys.exit("No knowledge cluster files found in the container.")

    for parquet, out_dir in targets:
        n = export(parquet, out_dir, args.full)
        print(f"{n:>3} clusters -> {out_dir / 'clusters.csv'}")


if __name__ == "__main__":
    main()
