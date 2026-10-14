"""Merge draft_*.jsonl into questions.csv (the human-editable master question set).

Checks that every gold_source_file exists in the corpus tier and that each
gold_passage really appears in that file's extracted text. A passage may be
several quotes joined with " | "; each one is checked separately.

Independent verification results in verification/compare_*.jsonl are merged
in as verify_* columns. review_status values already set in questions.csv
(human review) are kept across rebuilds.

Usage:
  python poc/questions/build_questions.py [--tier S]
  python poc/questions/build_questions.py --blind 3   # also write verification/blind_<n>.jsonl
                                                      # (id + question only) in 3 batches
"""
import argparse
import csv
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
POC = HERE.parent
VERIFY_DIR = HERE / "verification"
COLS = ["id", "question", "type", "pair_id", "gold_answer", "gold_source_file",
        "gold_passage", "notes", "review_status",
        "verify_status", "verify_answer", "verify_source_file", "verify_note"]


def norm(s):
    return re.sub(r"\s+", " ", s or "").strip().lower()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tier", default="S")
    ap.add_argument("--blind", type=int, metavar="N",
                    help="Write question-only files for blind verification in N batches")
    args = ap.parse_args()

    corpus = {p.name for p in (POC.parent / "poc_docs" / args.tier).iterdir()}
    text_dir = POC / "corpus" / f"text_{args.tier}"

    prev_review = {}
    if (HERE / "questions.csv").exists():
        prev_review = {r["id"]: r.get("review_status", "")
                       for r in csv.DictReader(open(HERE / "questions.csv", encoding="utf-8-sig"))}
    verify = {}
    for f in sorted(VERIFY_DIR.glob("compare_*.jsonl")):
        for line in open(f, encoding="utf-8"):
            if line.strip():
                v = json.loads(line)
                verify[v["id"]] = v

    corrections = {}
    corrections_path = VERIFY_DIR / "approved_corrections.jsonl"
    if corrections_path.exists():
        for line in corrections_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                correction = json.loads(line)
                if correction["id"] in corrections:
                    raise ValueError(f"duplicate approved correction: {correction['id']}")
                changes = correction["changes"]
                allowed = {"question", "gold_answer", "gold_source_file", "gold_passage", "notes"}
                if set(changes) - allowed:
                    raise ValueError(f"unsupported corrected fields for {correction['id']}")
                corrections[correction["id"]] = changes

    rows, problems = [], []
    for draft in sorted(HERE.glob("draft_*.jsonl")):
        for line in open(draft, encoding="utf-8"):
            if not line.strip():
                continue
            q = json.loads(line)
            q.update(corrections.get(q["id"], {}))
            q["review_status"] = prev_review.get(q["id"]) or q.get("review_status") or "auto_drafted"
            v = verify.get(q["id"], {})
            q.update({"verify_status": v.get("status", ""), "verify_answer": v.get("blind_answer", ""),
                      "verify_source_file": v.get("blind_source_file", ""),
                      "verify_note": v.get("note", "")})
            files = [f.strip() for f in (q.get("gold_source_file") or "").split(";") if f.strip()]
            for f in files:
                if f not in corpus:
                    problems.append(f"{q['id']}: gold file not in corpus: {f}")
            if q.get("gold_passage") and files:
                texts = " ".join(norm((text_dir / f"{f}.txt").read_text(encoding="utf-8", errors="replace"))
                                 for f in files if (text_dir / f"{f}.txt").exists())
                # A passage may be several quotes joined with " | ".
                for frag in q["gold_passage"].split(" | "):
                    if norm(frag) not in texts:
                        problems.append(f"{q['id']}: passage fragment not found verbatim: {frag[:60]}")
            rows.append({c: q.get(c, "") for c in COLS})

    ids = [r["id"] for r in rows]
    for dup in {i for i in ids if ids.count(i) > 1}:
        problems.append(f"duplicate id {dup}")

    for unknown in (set(corrections) | set(verify)) - set(ids):
        problems.append(f"verification/correction references unknown id {unknown}")
    if problems:
        print("\n".join(problems), file=sys.stderr)
        raise SystemExit("Validation failed; questions.csv was not overwritten.")

    temporary = HERE / "questions.csv.tmp"
    with open(temporary, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=COLS)
        w.writeheader()
        w.writerows(rows)
    temporary.replace(HERE / "questions.csv")

    if args.blind:
        VERIFY_DIR.mkdir(exist_ok=True)
        for b in range(args.blind):
            with open(VERIFY_DIR / f"blind_{b + 1}.jsonl", "w", encoding="utf-8") as f:
                for r in rows[b::args.blind]:
                    f.write(json.dumps({"id": r["id"], "question": r["question"]},
                                       ensure_ascii=False) + "\n")

    by_type, by_verify = {}, {}
    for r in rows:
        by_type[r["type"]] = by_type.get(r["type"], 0) + 1
        by_verify[r["verify_status"] or "-"] = by_verify.get(r["verify_status"] or "-", 0) + 1
    print(f"{len(rows)} questions -> {HERE / 'questions.csv'}  {by_type}")
    print(f"verification: {by_verify}")
    print("\n".join(problems) if problems else "All gold files and passages verified.")


if __name__ == "__main__":
    main()
