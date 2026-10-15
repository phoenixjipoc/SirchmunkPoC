# A/B/C execution record

81 raw files; 120 verified questions per stage; DEEP mode. A=k10/reuse off, B=k5/off, C=k10/on at similarity 0.85. Each stage starts with an empty cluster store; parsed-text cache is shared.

Search receives only IDs/questions. References and acceptance criteria are used later for automated scoring and separate review.

## Stage timing

| Stage | Started | Completed | Questions | Clusters |
| --- | --- | --- | --- | --- |
| A | 2026-10-14T12:51:31+08:00 | 2026-10-14T14:19:16+08:00 | 120 | 82 |
| B | 2026-10-14T14:20:15+08:00 | 2026-10-14T15:42:08+08:00 | 120 | 76 |
| C | 2026-10-14T15:43:01+08:00 | 2026-10-14T17:06:15+08:00 | 120 | 80 |

Times are recorded with the +08:00 offset. Stage completion includes export; reviews and final adjudication follow.

## Recorded incidents

- The legacy DOC produced partially garbled text; it remained unchanged across all stages.
- A completed search and grading before a Unicode JSONL export failure. Only export parsing was repaired; search was not rerun.
- An early repair event prematurely claimed a test pass. The later `export_regression_test_passed` event records the actual result.
- C/SVC-03 recovered through an automatic connection retry. Its timing and usage remain included.
- CONS-16 took a direct-document route with a separate five-file default and missed the ten named RFPs.
- Final review resolved all required disagreements; original labels were preserved.

## Completion and source records

360 responses, 190 required reviews resolved, and 238 clusters exported. Final correct counts: A=74, B=68, C=75.

[events.jsonl](events.jsonl) retains all 48 events, commands, timestamps, and incident details. One parser-followup event has no recorded timestamp. [validation.json](validation.json) contains the original integrity checks.

Recorded commands refer to the original workspace. Use the [reproduction guide](../../../docs/REPRODUCING.md) for a new checkout.
