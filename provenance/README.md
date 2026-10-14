# Publication provenance

This is an English publication of an existing local PoC, not a new evaluation run.

`source_inventory.json` lists every copied source artifact and its pre-publication SHA-256. The copy includes the 81 original documents, question drafts and audits, all existing result directories, logs, scripts, and the original ZIP. Python bytecode/cache directories and installed audit dependencies are excluded because they are environment artifacts rather than test data.

Original evidence files remain byte-for-byte unchanged. The listed narrative documents were replaced with English editions; their original bytes are preserved at the same relative path under `original_documentation/`. English presentation CSVs are additional files under `reports/verified120/`, not replacements for the raw answers or frozen judge records.

`publication_validation.json` records checks on copied hashes, references, record counts, grades, English translations, local document links, and credential-pattern scanning. These are publication checks, separate from the experiment's original validation and semantic grading.

The translation map under `tools/english_translations.json` contains the one Chinese generated answer (C / INV-04) and its cluster summary. Original text hashes guard against applying a translation to changed evidence. Translation does not change numeric facts, grades, timings, or token counts. English diagnostic labels replace Chinese explanatory hints only in presentation tables.

Historical raw logs and frozen scripts can contain Chinese library messages. The legacy DOC's malformed extraction must also remain intact as evidence of a parser limitation. These preserved bytes are not untranslated English report prose.
