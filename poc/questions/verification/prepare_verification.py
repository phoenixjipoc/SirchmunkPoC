"""Freeze the inputs and extract original PDFs/DOCX for an independent audit."""
import hashlib
import json
import re
import shutil
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

import fitz

HERE = Path(__file__).resolve().parent
QUESTIONS = HERE.parent
ROOT = QUESTIONS.parents[1]
AUDIT = HERE / "audit_20261014"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def docx_text(path):
    ns = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
    sections = []
    with zipfile.ZipFile(path) as archive:
        names = ["word/document.xml"] + sorted(n for n in archive.namelist()
                  if re.fullmatch(r"word/(header\d+|footer\d+|footnotes|endnotes)\.xml", n))
        for name in names:
            tree = ET.fromstring(archive.read(name))
            paragraphs = ["".join(t.text or "" for t in p.findall(".//w:t", ns))
                          for p in tree.findall(".//w:p", ns)]
            sections.append(f"[{name}]\n" + "\n".join(paragraphs))
    return "\n".join(sections)


def main():
    snapshot = AUDIT / "original"
    extracted = AUDIT / "source_text"
    snapshot.mkdir(parents=True, exist_ok=True)
    extracted.mkdir(exist_ok=True)
    for path in [QUESTIONS / "questions.csv", *QUESTIONS.glob("draft_*.jsonl")]:
        target = snapshot / path.name
        if not target.exists():
            shutil.copy2(path, target)
    inventory = []
    for path in sorted((ROOT / "poc_docs" / "S").iterdir()):
        if not path.is_file():
            continue
        item = {"file": path.name, "sha256": sha256(path), "bytes": path.stat().st_size}
        try:
            if path.suffix.lower() == ".pdf":
                with fitz.open(path) as doc:
                    parts = [f"\n[PDF page {i + 1}]\n" + page.get_text(sort=True)
                             for i, page in enumerate(doc)]
                    item.update(method="PyMuPDF from original PDF", pages=len(doc))
                text = "".join(parts)
            elif path.suffix.lower() == ".docx":
                text = docx_text(path)
                item.update(method="DOCX body, headers, footers, and notes XML from original")
            else:
                item.update(method="unsupported legacy format; consult original/previous extraction",
                            review_required=True)
                inventory.append(item)
                continue
            target = extracted / (path.name + ".txt")
            target.write_text(text, encoding="utf-8")
            item.update(chars=len(text), text_sha256=sha256(target))
        except Exception as exc:
            item.update(error=str(exc), review_required=True)
        inventory.append(item)
    (AUDIT / "source_inventory.json").write_text(json.dumps(inventory, indent=2), encoding="utf-8")
    frozen = [{"file": p.name, "sha256": sha256(p)} for p in sorted(snapshot.iterdir())]
    (AUDIT / "input_hashes.json").write_text(json.dumps(frozen, indent=2), encoding="utf-8")
    print(json.dumps({"sources": len(inventory), "extracted": len(list(extracted.glob('*.txt'))),
                      "needs_special_reading": [x['file'] for x in inventory if x.get('review_required')],
                      "snapshot": str(snapshot)}, indent=2))


if __name__ == "__main__":
    main()
