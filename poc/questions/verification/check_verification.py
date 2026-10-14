"""Check audit coverage and quoted evidence without claiming semantic correctness.

Usage: python poc/questions/verification/check_verification.py [--complete]
The report is safe to run while independent reviewers are saving progress.
"""
import argparse
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path

import fitz

HERE = Path(__file__).resolve().parent
AUDIT = HERE / "audit_20261014"
ROOT = HERE.parents[2]


def norm(text):
    text = unicodedata.normalize("NFKC", str(text)).casefold()
    text = text.translate(str.maketrans({"\u2019": "'", "\u2018": "'", "\u201c": '"',
                                       "\u201d": '"', "\u2013": "-", "\u2014": "-", "\u00ad": ""}))
    return re.sub(r"\s+", " ", text).strip()


def load(path):
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip()]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--complete", action="store_true")
    args = ap.parse_args()
    errors, quote_checks, batches = [], [], []
    source_cache, page_cache, native_cache, metadata_cache = {}, {}, {}, {}
    for batch in range(1, 4):
        expected = {q["id"]: q["question"] for q in load(HERE / f"blind_{batch}.jsonl")}
        answers = load(AUDIT / f"blind_answers_{batch}.jsonl")
        compared = load(AUDIT / f"compare_{batch}.jsonl")
        batches.append({"batch": batch, "expected": len(expected), "blind_answers": len(answers),
                        "compared": len(compared), "statuses": dict(Counter(r["status"] for r in compared))})
        for kind, rows in [("blind", answers), ("compare", compared)]:
            counts = Counter(r["id"] for r in rows)
            if any(n != 1 for n in counts.values()):
                errors.append(f"batch {batch} {kind}: duplicate ids")
            if set(counts) - set(expected):
                errors.append(f"batch {batch} {kind}: unexpected ids {set(counts) - set(expected)}")
            if args.complete and set(counts) != set(expected):
                errors.append(f"batch {batch} {kind}: missing {sorted(set(expected) - set(counts))}")
        evidence_rows = [("blind", row) for row in answers] + [("compare", row) for row in compared]
        for kind, row in evidence_rows:
            if kind == "blind" and row.get("question") != expected.get(row["id"]):
                errors.append(f"{row['id']}: blind question differs from input")
            if not row.get("blind_answer"):
                errors.append(f"{row['id']}: missing independent answer")
            for ev in row.get("evidence", []):
                file, quote = ev.get("file", ""), ev.get("quote", "")
                if not file or Path(file).name != file or not (ROOT / "poc_docs" / "S" / file).is_file():
                    errors.append(f"{row['id']}: invalid source {file}")
                    continue
                if file not in source_cache:
                    paths = [AUDIT / "source_text" / (file + ".txt"),
                             ROOT / "poc" / "corpus" / "text_S" / (file + ".txt")]
                    source_cache[file] = [(str(p.relative_to(ROOT)), norm(p.read_text(encoding="utf-8", errors="replace")))
                                          for p in paths if p.exists()]
                matches = [p for p, text in source_cache[file] if quote and norm(quote) in text]
                page_match, actual_pages = None, []
                if file.endswith('.pdf'):
                    if file not in page_cache:
                        raw = (AUDIT / 'source_text' / (file + '.txt')).read_text(encoding='utf-8')
                        split = re.split(r'\[PDF page (\d+)\]', raw)
                        page_cache[file] = {int(split[i]): norm(split[i+1]) for i in range(1,len(split),2)}
                    actual_pages = [p for p,t in page_cache[file].items() if quote and norm(quote) in t]
                    # Coordinate sorting can intermingle headings/watermarks or OCR lines.
                    # Check the original PDF's native text order before calling it missing.
                    if not actual_pages:
                        if file not in native_cache:
                            with fitz.open(ROOT / 'poc_docs' / 'S' / file) as doc:
                                native_cache[file] = {i+1: norm(p.get_text(sort=False)) for i,p in enumerate(doc)}
                                metadata_cache[file] = doc.metadata
                        actual_pages = [p for p,t in native_cache[file].items() if quote and norm(quote) in t]
                        if actual_pages:
                            matches.append(f'poc_docs/S/{file} (PDF native text order)')
                    if isinstance(ev.get('page'), int):
                        page_match = ev['page'] in actual_pages if actual_pages else None
                    elif str(ev.get('page', '')).startswith('PDF metadata:'):
                        if quote and any(norm(quote) in norm(v) for v in metadata_cache.get(file, {}).values()):
                            matches.append(f'poc_docs/S/{file} (PDF metadata)')
                quote_checks.append({"stage": kind, "id": row["id"], "file": file, "page": ev.get("page"),
                                     "match": bool(matches), "matched_text": matches,
                                     "page_match": page_match, "actual_pages": actual_pages,
                                     "quote": quote})
        for row in compared:
            if row["status"] not in {"verified", "needs_correction", "ambiguous", "unverifiable"}:
                errors.append(f"{row['id']}: unsupported independent status {row['status']}")
    report = {"batches": batches, "errors": errors, "quote_count": len(quote_checks),
              "quote_matches": sum(x["match"] for x in quote_checks),
              "quotes_by_stage": dict(Counter(x['stage'] for x in quote_checks)),
              "page_mismatches": sum(x['page_match'] is False for x in quote_checks),
              "pdf_page_locators_unchecked": sum(x['file'].endswith('.pdf') and isinstance(x['page'], int) and x['page_match'] is None for x in quote_checks),
              "quote_checks": quote_checks,
              "note": "Text matching is a provenance check, not a proof that the answer is semantically correct. Page locators require reviewer checking."}
    (AUDIT / "mechanical_checks.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in report.items() if k not in {"quote_checks", "note"}}, ensure_ascii=False, indent=2))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
