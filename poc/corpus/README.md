# Public test corpus (S tier)

81 public documents, kept in their original format (78 PDF, 2 DOCX, 1 DOC), in `poc_docs/S/`.
Mostly US public pension fund RFPs, plus industry DDQ templates (ILPA, INREV, PRI, AC Private Markets).

- `candidates.csv`: source list (issuer, category, year, URL)
- `download.py`: downloads candidates into `poc_docs/<tier>/`; re-runs skip files already downloaded
- `manifest_S.csv`: result per candidate (file name, status, size, sha256)

Built-in near-duplicates:
- 23 investment consultant RFPs from different funds (same structure, different numbers)
- Same issuer across years: Hawaii ERS PE 2013/2022, real estate 2017/2022; TRS Illinois 2023/2025; Oklahoma OPERS 2022/2023
- Versioned DDQs: ILPA DDQ v1.2 (2018) and 2.0 (2021); INREV FoF DDQ 2018 and 2022; ILPA ESG FAQ 2021 and 2024

Every PDF has an extractable text layer (`pdftotext` gives at least 200 words each). There are no scanned-only files.

## Loading into Sirchmunk

The container has no volume mounts, so the corpus is copied in:

```bash
MSYS_NO_PATHCONV=1 docker exec sirchmunk mkdir -p /mnt/docs
MSYS_NO_PATHCONV=1 docker cp poc_docs/S sirchmunk:/mnt/docs/
```

Recreating the container removes the copied corpus, so copy it again after any recreate.
