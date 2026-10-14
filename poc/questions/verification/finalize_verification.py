"""Publish complete independent reviews and explicit adjudications to the dataset.

Requires all 120 blind answers and comparisons. Disputed questions require an
entry in audit_20261014/adjudications.jsonl; suggested edits are never auto-applied.
"""
import csv
import hashlib
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

from check_verification import AUDIT, HERE, load


def write_jsonl(path, rows):
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
    temp.replace(path)


def main():
    subprocess.run([sys.executable, str(HERE / "check_verification.py"), "--complete"], check=True)
    checks = json.loads((AUDIT / "mechanical_checks.json").read_text(encoding="utf-8"))
    if (checks["quote_matches"] != checks["quote_count"] or checks.get('page_mismatches')
            or checks.get('pdf_page_locators_unchecked')):
        raise SystemExit("Resolve unmatched evidence quotations before publishing.")
    frozen_hashes = json.loads((AUDIT / 'blind_answer_hashes.json').read_text(encoding='utf-8'))
    for record in frozen_hashes:
        if hashlib.sha256((AUDIT / record['file']).read_bytes()).hexdigest() != record['sha256']:
            raise SystemExit('Frozen blind answers changed: ' + record['file'])
    decisions = load(AUDIT / "adjudications.jsonl")
    adjudicated = {r["id"]: r for r in decisions}
    if len(adjudicated) != len(decisions):
        raise SystemExit("Duplicate adjudications")
    originals = list(csv.DictReader((AUDIT / "original" / "questions.csv").open(encoding="utf-8-sig")))
    original_map = {r["id"]: r for r in originals}
    finals, corrections = [], []
    for batch in range(1, 4):
        blind = {r['id']: r for r in load(AUDIT / f'blind_answers_{batch}.jsonl')}
        for review in load(AUDIT / f"compare_{batch}.jsonl"):
            qid = review["id"]
            if review['blind_answer'] != blind[qid]['blind_answer']:
                raise SystemExit('Comparison changed frozen independent answer: ' + qid)
            decision = adjudicated.get(qid)
            if review["status"] != "verified" and not decision:
                raise SystemExit(f"Missing adjudication: {qid} ({review['status']})")
            final = dict(review)
            if decision:
                final["status"] = decision["status"]
                final["note"] = review["note"] + " | Adjudication: " + decision["note"]
                changes = decision.get("changes", {})
                if changes:
                    corrections.append({"id": qid, "changes": changes, "reason": decision["note"],
                                        "original": {k: original_map[qid][k] for k in changes}})
            if final["status"] not in {"verified", "corrected", "needs_human_review", "unverifiable"}:
                raise SystemExit(f"Invalid final status: {qid}: {final['status']}")
            final["note"] += " | Acceptance: " + str(review.get("acceptance_notes", ""))
            final["audit_date"] = "2026-10-14"
            final["human_verified"] = False
            finals.append(final)
    if set(adjudicated) - {r['id'] for r in finals}:
        raise SystemExit("Unknown adjudication id")
    write_jsonl(HERE / "compare_audit_20261014.jsonl", finals)
    write_jsonl(HERE / "approved_corrections.jsonl", corrections)
    subprocess.run([sys.executable, str(HERE.parent / "build_questions.py")], check=True)
    questions_path = HERE.parent / "questions.csv"
    with questions_path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fields, rows = reader.fieldnames, list(reader)
    ready = [r for r in rows if r['verify_status'] in {'verified', 'corrected'}]
    target = HERE.parent / "questions_verified.csv"
    with target.open('w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(ready)
    counts = dict(Counter(r['status'] for r in finals))
    manifest = {"date": "2026-10-14", "reviewed": len(finals), "ready_for_evaluation": len(ready),
                "statuses": counts, "source_documents": 81, "blind_batches": 3,
                "source_inventory": "audit_20261014/source_inventory.json",
                "questions_sha256": hashlib.sha256(questions_path.read_bytes()).hexdigest(),
                "verified_subset_sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
                "corrected_ids": [r['id'] for r in corrections],
                "excluded_ids": [r['id'] for r in rows if r['verify_status'] not in {'verified','corrected'}],
                "human_reviewed": False,
                "limitations": "Independent AI blind verification, not human review. Original evaluation scores are not regraded."}
    (AUDIT / "completion.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
