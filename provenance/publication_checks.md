# Publication checks

Rechecked October 15, 2026 for the verified 120-question publication.

| Check | Command | Result |
|---|---|---|
| English tables and reports | `python tools/build_english_reports.py` | 14 tables from 360 recorded answers |
| Campaign archive | `python tools/export_campaign.py` | 473 files, including three English reports |
| Evidence, wording, links, and archive | `python tools/verify_publication.py` | See `publication_validation.json` |
| Harness regression checks | `python -m unittest discover -s poc -p "test_*.py"` | Six passed |

The retained evidence includes 81 original documents, all six question drafts, 360 responses, 190 required reviews, and 238 clusters. These offline checks do not rerun search or reassess answer correctness.
