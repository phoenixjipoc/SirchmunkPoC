"""Download public RFP/DDQ documents listed in candidates.csv into poc_docs/<tier>/.

Files are kept in their original format (PDF/DOC/DOCX), no conversion.
Writes manifest.csv with one row per candidate (status ok/failed, sha256, size).

Usage: python download.py [--tier S]
"""
import argparse
import csv
import hashlib
import re
from pathlib import Path
from urllib.parse import unquote, urlparse

import requests
import truststore

# Use the Windows certificate store so TLS works behind the corporate proxy.
truststore.inject_into_ssl()

HERE = Path(__file__).parent
ROOT = HERE.parent.parent
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")

MAGIC = {b"%PDF": ".pdf", b"PK\x03\x04": ".docx", b"\xd0\xcf\x11\xe0": ".doc"}


def detect_ext(head: bytes):
    for sig, ext in MAGIC.items():
        if head.startswith(sig):
            return ext
    return None


def safe_name(issuer, url, ext):
    stem = Path(unquote(urlparse(url).path)).stem or "document"
    stem = re.sub(r"\.(pdf|docx?)$", "", stem, flags=re.I)
    stem = re.sub(r"[^A-Za-z0-9._-]+", "_", stem).strip("_")[:80]
    return f"{issuer}__{stem}{ext}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tier", default="S")
    args = ap.parse_args()

    out_dir = ROOT / "poc_docs" / args.tier
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = list(csv.DictReader(open(HERE / "candidates.csv", encoding="utf-8")))
    seen_hashes = {}
    manifest = []
    manifest_path = HERE / f"manifest_{args.tier}.csv"
    # Re-runs skip files that were already downloaded.
    prev = {}
    if manifest_path.exists():
        prev = {m["url"]: m["file"] for m in csv.DictReader(open(manifest_path, encoding="utf-8"))
                if m["status"] == "ok"}

    for i, r in enumerate(rows, 1):
        rec = {**r, "file": "", "status": "", "bytes": 0, "sha256": "", "note": ""}
        try:
            if (out_dir / prev.get(r["url"], "\0")).is_file():
                data = (out_dir / prev[r["url"]]).read_bytes()
                digest = hashlib.sha256(data).hexdigest()
                seen_hashes[digest] = prev[r["url"]]
                rec.update(file=prev[r["url"]], status="ok", bytes=len(data), sha256=digest)
                manifest.append(rec)
                continue
            host = urlparse(r["url"]).netloc
            resp = requests.get(r["url"], timeout=60, headers={
                "User-Agent": UA, "Accept": "application/pdf,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9", "Referer": f"https://{host}/"})
            resp.raise_for_status()
            data = resp.content
            ext = detect_ext(data[:8])
            if not ext:
                raise ValueError(f"not a PDF/DOC/DOCX (content-type {resp.headers.get('content-type')})")
            digest = hashlib.sha256(data).hexdigest()
            if digest in seen_hashes:
                raise ValueError(f"exact duplicate of {seen_hashes[digest]}")
            name = safe_name(r["issuer"], r["url"], ext)
            (out_dir / name).write_bytes(data)
            seen_hashes[digest] = name
            rec.update(file=name, status="ok", bytes=len(data), sha256=digest)
        except Exception as e:
            rec.update(status="failed", note=str(e)[:200])
        manifest.append(rec)
        print(f"[{i:>2}/{len(rows)}] {rec['status']:6} {rec['file'] or r['url']} {rec['note']}")

    with open(manifest_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(manifest[0].keys()))
        w.writeheader()
        w.writerows(manifest)
    ok = sum(m["status"] == "ok" for m in manifest)
    print(f"\n{ok}/{len(manifest)} downloaded to {out_dir}")


if __name__ == "__main__":
    main()
