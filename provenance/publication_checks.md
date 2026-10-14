# Publication checks

The repository was checked before its initial publication on October 14, 2026.

| Check | Command | Result |
|---|---|---|
| English presentation generation | `python tools/build_english_reports.py` | 14 presentation CSVs generated from 360 recorded results; no model calls |
| Corpus, source inventory, translations, record coverage, local links, credential patterns, and file sizes | `python tools/verify_publication.py` | Passed; detailed counts and hashes are recorded in `publication_validation.json` and `source_inventory.json` |
| Existing harness regression tests | `python -m unittest discover -s poc -p "test_*.py"` | 6 tests passed |

These are offline publication and harness checks. They do not constitute a new search experiment or a new independent semantic review of the model answers. The raw campaign and question-verification records are preserved separately.
