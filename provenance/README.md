# Publication provenance

This is the English publication of the verified 120-question A/B/C PoC. Repository cleanup and documentation updates do not constitute new evaluation runs.

`source_inventory.json` lists the retained source artifacts for this campaign and their pre-publication SHA-256 values. It includes the 81 original documents, all six question drafts, the 120-question audit, campaign records, logs, and supporting scripts. Unrelated experiments, obsolete reports, and non-English report copies are excluded. Python bytecode/cache directories and installed audit dependencies are environment artifacts rather than test data.

Original evidence files remain byte-for-byte unchanged. Retained copied Markdown documents have a `publication_sha256` and `publication_bytes` recording their current English editions; their `source_sha256` records the pre-publication fingerprint only. Superseded narrative copies are not included. English presentation CSVs are additional files under `reports/verified120/`, not replacements for raw answers or frozen judge records.

The campaign ZIP is a generated publication artifact, tracked separately by `poc/results/20261014_ABC_verified120_export.manifest.json`. It contains the current campaign files, with English narratives and unchanged raw evidence. It is not the original pre-translation archive. The export utility is deterministic for unchanged file contents; the verifier checks its checksum, exact member set, and every member's content.

`publication_validation.json` records checks on retained hashes, references, record counts, grades, English translations, all repository Markdown documents, local links, archive consistency, and credential-pattern scanning. These are publication checks, separate from the experiment's original validation and semantic grading.

The translation map under `tools/english_translations.json` contains the one Chinese generated answer (C / INV-04) and its cluster summary. Original text hashes guard against applying a translation to changed evidence. Translation does not change numeric facts, grades, timings, or token counts. English diagnostic labels replace Chinese explanatory hints only in presentation tables.

Raw logs and frozen scripts can contain Chinese library messages. The legacy DOC's malformed extraction must also remain intact as evidence of a parser limitation. These preserved bytes are not untranslated report prose. Repository narrative documentation and archive narratives are English; the English result tables include explicit translation notes where needed.
