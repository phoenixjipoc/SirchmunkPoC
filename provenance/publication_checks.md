# Publication checks

The repository was rechecked on October 15, 2026 after restricting it to the verified 120-question campaign and English narrative documentation.

| Check | Command | Result |
|---|---|---|
| English presentation generation | `python tools/build_english_reports.py` | 14 presentation CSVs generated from 360 recorded results; no model calls |
| Campaign archive generation | `python tools/export_campaign.py` | 473 campaign files packaged with three English narrative reports; original evidence retained |
| Corpus, retained inventory, translations, record coverage, English narratives, ZIP contents, local links, credential patterns, and file sizes | `python tools/verify_publication.py` | Detailed results are recorded in `publication_validation.json`; retained source and English-edition hashes are in `source_inventory.json` |
| Existing harness regression tests | `python -m unittest discover -s poc -p "test_*.py"` | 6 tests passed |

These are offline publication and harness checks. They do not constitute a new search experiment or a new independent semantic review of the model answers. The raw campaign and question-verification records are preserved separately.

The cleanup removed obsolete experiments and non-English report copies from the current repository tree. All six draft batches remain because they are inputs to the final 120-question audit. The 81-file corpus, 360 recorded answers, original grades and reviews, and 238 exported knowledge clusters retain their original evidence bytes. The refreshed ZIP contains current English reports, rather than superseded narrative copies.
