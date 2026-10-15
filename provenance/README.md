# Publication provenance

This repository retains the verified 120-question campaign and English documentation. Packaging changes do not rerun the experiment.

- `source_inventory.json` lists 814 retained source artifacts. Original evidence uses `source_sha256`; copied Markdown uses `publication_sha256` and `publication_bytes` for its current English edition.
- Original documents, answers, grades, logs, drafts, and audit records retain their bytes. Superseded narrative copies and unrelated experiments are excluded.
- The campaign ZIP contains the current 473 campaign files. Its adjacent manifest records size and checksum; the verifier compares every member with the directory.
- `reports/verified120/` provides English presentation tables. `tools/english_translations.json` guards translations with original-text hashes; no grade, numeric result, or timing is changed.
- `publication_validation.json` records integrity, language, links, archive, and credential-pattern checks. These checks are separate from answer scoring.

All narrative documents are English. Raw outputs may retain original multilingual text or parser corruption. C/INV-04 and its cluster have explicit English translations for presentation. Raw evidence is preserved for traceability.
