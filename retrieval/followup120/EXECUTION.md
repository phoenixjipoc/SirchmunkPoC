# Execution record

## Frozen setup

- Original 120 questions and 81 source hashes retained.
- R1 artifacts copied byte-for-byte into the frozen input package.
- Retrieval adapter, installed package hashes, prompts and seeds frozen before the first new request.
- Four inherited runtime checks and five follow-up metric/ranking checks passed.
- Baseline replay integration reproduced 51/74/80 hits and zero artificial changes for identical runs.

## Recovery

- R2 stopped on a temporary container DNS failure at SVC-21. The first 44 valid results were hashed and retained. Host DNS and TCP succeeded; container DNS recovered without configuration changes.
- A second container DNS interruption occurred at XD-09. An external launcher now retries native DNS through the host-resolved addresses only when native resolution fails. The configured hostname, SNI, TLS verification, credentials and frozen search implementation remain unchanged. Transport events and address-resolution timestamps are retained.
- Technical attempts stay in the raw logs. Completed misses are not retried. These incidents prevent treating elapsed wall time as clean service latency.

## Evidence checks

- Source anchors: 358 normalized text matches and two rendered-page checks, covering all 360 retained quotations.
- Legacy Word extraction reproduced 85,278 characters and the audited text hash after CRLF/LF normalization. The custom adapter is limited to the exact frozen source.
- The parser repair remains separate from R2/R3, S and D.
- New source checks use four workers after timed retrieval. This resource setting was finalized before source checking began; prompts and acceptance rules remain unchanged.

## Snapshot clarification

The frozen S implementation passes the directory snapshot's `full_content` field as well as titles, metadata and previews. Eight of the 81 entries contain cached full text, up to 15,008 characters; previews reach 800 characters. The plan's metadata/preview wording was incomplete. Results describe the actual snapshot inputs. No retrieval code or candidate content was changed after execution began.

## Parser correction

The first P/P0 replay patched the unused synchronous executor. The real keyword tool uses the asynchronous executor, so the initial comparison did not enable the repair. It is archived and excluded from final scores. See [the correction record](PARSER_CORRECTION.md).

The corrected driver passed an integration check through the real keyword tool: the legacy file was found with the adapter and absent without it. Both corrected arms use fixed file-path order to remove the native ordering variation observed in 73 initial query pairs. Original questions, keyword terms, directory outputs and source files are retained.

The first source-check stage completed 599 new or upgraded associations with four workers. Sixteen records contained non-verbatim quotations in negative decisions. Direct source review retained all sixteen negative classifications and supplied grounded evidence; one document required inspection of all ten rendered pages. Original check records remain intact.

## Completion

R2, R3, S and D each completed 120 questions. Corrected P0 and P each completed 120 keyword replays; non-legacy candidate membership and relative order matched on every question. The repaired source appeared on thirteen queries, including rank two for XD-16. That question's required-source coverage increased from zero to one of four.

After corrected replay, the final pool contained 974 unlisted associations: 411 baseline decisions and 563 follow-up decisions. Of the latter, 493 were retained from the initial source-check stage and seventy required new checks. The final pool has no unresolved support classifications. Earlier unused checks remain recorded in total request usage.

All 74 artifact checks passed, including question IDs, frozen inputs, runtime identifiers, exact candidate permutations, parser integration, source evidence and score invariants. A separate environment check confirmed the original corpus, installed source hashes, deployed scripts and container image. See the [final report](reports/REPORT.md).
