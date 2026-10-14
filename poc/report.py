"""Aggregate judged runs into question-type x mode x tier tables -> poc/results/report.md

Usage: python poc/report.py [run_id ...]   (default: every run with results_judged.csv)
"""
import csv
import json
import statistics
import sys
from pathlib import Path

RESULTS = Path(__file__).parent / "results"
TYPE_ORDER = ["detail", "pair_a", "pair_b", "medium", "broad", "unanswerable"]


def pct(n, d):
    return f"{100 * n / d:.0f}%" if d else "-"


def p95(xs):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(round(0.95 * (len(xs) - 1))))] if xs else 0


def summarize(rows):
    n = len(rows)
    lab = [r["judge_label"] for r in rows]
    gold_rows = [r for r in rows if r["gold_in_candidates"] != ""]
    lat = [float(r["latency_s"]) for r in rows]
    return {
        "n": n,
        "correct": pct(lab.count("correct") + lab.count("correct_refusal"), n),
        "partial": pct(lab.count("partial"), n),
        "wrong": pct(lab.count("wrong") + lab.count("hallucinated"), n),
        "no_answer": pct(lab.count("no_answer"), n),
        "gold@cand": pct(sum(r["gold_in_candidates"] == "True" for r in gold_rows), len(gold_rows)),
        "gold@sampled": pct(sum(r["gold_in_sampled"] == "True" for r in gold_rows), len(gold_rows)),
        "gold@evidence": pct(sum(r["gold_in_evidence"] == "True" for r in gold_rows), len(gold_rows)),
        "p50_s": f"{statistics.median(lat):.0f}" if lat else "-",
        "p95_s": f"{p95(lat):.0f}",
        "tokens": f"{statistics.mean(int(r['total_tokens'] or 0) for r in rows):,.0f}" if rows else "-",
    }


def table(groups):
    cols = ["n", "correct", "partial", "wrong", "no_answer", "gold@cand", "gold@sampled",
            "gold@evidence", "p50_s", "p95_s", "tokens"]
    out = ["| group | " + " | ".join(cols) + " |", "|---" * (len(cols) + 1) + "|"]
    for name, rows in groups:
        s = summarize(rows)
        out.append(f"| {name} | " + " | ".join(str(s[c]) for c in cols) + " |")
    return "\n".join(out)


def main():
    run_dirs = [RESULTS / r for r in sys.argv[1:]] or sorted(
        d for d in RESULTS.iterdir() if (d / "results_judged.csv").exists())
    md = ["# Sirchmunk PoC results", "",
          "Columns: correct includes correct refusals on unanswerable questions; wrong includes "
          "hallucinations. gold@cand/sampled/evidence = the gold file was among the retrieval "
          "candidates / among the files sampled for evidence (top_k_files) / in the final evidence. "
          "Latency in seconds; tokens = mean total LLM tokens per question.", ""]
    for d in run_dirs:
        meta = json.loads((d / "run_meta.json").read_text(encoding="utf-8"))
        rows = list(csv.DictReader(open(d / "results_judged.csv", encoding="utf-8-sig")))
        md.append(f"## {meta['run_id']}")
        md.append(f"tier {meta['tier']} ({meta['n_files']} files), mode {meta['mode']}, "
                  f"cluster reuse {meta.get('cluster_reuse', True)} "
                  f"(threshold {meta.get('cluster_sim_threshold')}), "
                  f"top_k_files {meta.get('top_k_files') or 5}, "
                  f"model {meta['model']}, judge {meta.get('judge', {}).get('model', '?')}, "
                  f"warmup {meta.get('warmup', {})}")
        md.append("")
        groups = [("ALL", rows)] + [(t, [r for r in rows if r["type"] == t])
                                     for t in TYPE_ORDER if any(r["type"] == t for r in rows)]
        md.append(table(groups))
        blocked = [r for r in rows if r["judge_label"] == "no_answer"]
        usable = [r for r in blocked if r.get("pre_gate_label") in ("correct", "partial")]
        md.append("")
        md.append(f"- Summary gate blocked {len(blocked)} answers; {len(usable)} of them were "
                  f"correct/partial before the gate.")
        md.append(f"- rga timeouts: {sum(r['rga_timeout'] == 'True' for r in rows)}; "
                  f"cluster reuse hits: {sum(bool(r['reused_cluster']) for r in rows)}")
        pairs = {}
        for r in rows:
            if r["pair_id"]:
                pairs.setdefault(r["pair_id"], {})[r["type"]] = r
        both = [p for p in pairs.values() if "pair_a" in p and "pair_b" in p]
        md.append(f"- Pairs: {len(both)}; both correct: "
                  f"{sum(p['pair_a']['judge_label'] == p['pair_b']['judge_label'] == 'correct' for p in both)}; "
                  f"pair_b reused a cluster: {sum(bool(p['pair_b']['reused_cluster']) for p in both)}")
        md.append("")
    (RESULTS / "report.md").write_text("\n".join(md), encoding="utf-8")
    print("\n".join(md))


if __name__ == "__main__":
    main()
