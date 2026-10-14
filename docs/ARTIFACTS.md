# Artifact guide

## Main English entry points

`reports/verified120/report.md` and the CSVs beside it present the October 14 experiment in English. The original result records remain in `poc/results/20261014_ABC_verified120/`. Numerical scores and usage in the presentation tables are unchanged. One Chinese model answer has an explicit translation record.

| File or directory | Meaning |
|---|---|
| `poc_docs/S/` | Original 81-file search corpus: 78 PDF, two DOCX, one DOC |
| `poc/corpus/candidates.csv` | Public source list and URLs |
| `poc/corpus/manifest_S.csv` | Download status, names, sizes, hashes |
| `poc/corpus/text_S/` | Historical extracted text; not the raw search corpus |
| `poc/questions/draft_*.jsonl` | Preserved question-generation drafts |
| `poc/questions/questions_verified.csv` | Evaluation-ready 120-question reference snapshot |
| `poc/questions/verification/` | Blind inputs, corrections, source audit, and adjudications |
| `poc/harness/sirch_runner.py` | Container-side SDK runner and tracing |
| `poc/results/20261014_ABC_verified120/inputs/` | Frozen questions, corpus inventory, executable snapshots, effective defaults |
| `.../campaign.json` | A/B/C configuration, state, hashes, and exporter amendment |
| `.../test_process.md`, `events.jsonl` | English process narrative and original event history |
| `.../summary.csv` | Aggregate and question-type scores |
| `.../all_results.csv` | All 360 answers, primary/final labels, evidence, metrics |
| `.../question_comparison.csv` | The same 120 IDs across A, B, and C |
| `.../paired_results.csv` | 15 pairs per run, 45 comparison rows |
| `.../reuse_cases.csv` | All nine actual C reuse events with source question IDs and similarity |
| `.../reuse_matched_comparison.csv` | A and C on identical question-ID cohorts defined by C's reuse behavior |
| `.../failure_cases.csv` | All results that were not fully correct |
| `.../review_queue.csv` | The 190 required review records |
| `.../transition_summary.csv` | Correctness gains/regressions from A to B/C |
| `.../sensitivity.csv` | Scores excluding ambiguous SVC-15; does not replace the main scores |
| `.../validation.json` | Original structural and integrity validation |
| `.../export_status.json` | Completion of search, judging, and required reviews |

Within each `A`, `B`, or `C` directory:

- `run_meta.json`: effective model, image digest, paths, timing, configuration, and runner hash.
- `questions.jsonl`: search input containing only ID and question.
- `question_snapshot.csv`: full frozen reference, retained for later grading.
- `results.jsonl` / `results.csv`: recorded search answers and telemetry.
- `raw/<question-id>.json`: full context, logs, model-call usage, and tracing.
- `results_judged.csv` / `judge_records.jsonl`: original labels and resumable judge checkpoint.
- `review_decisions.jsonl`: final review decisions, append-only; the latest decision per ID applies.
- `secondary_review_records.jsonl`, `review_disagreements.jsonl`, `review_resolution.json`: separate reviews and final disagreement dispositions.
- `clusters.csv`: readable knowledge-cluster export.
- `clusters_full.jsonl`: full exported cluster records, with Unicode escaped losslessly.
- `live_results_snapshot.json`, where present: intermediate monitoring snapshot, not the authoritative final result count.

Cluster counts are A=82, B=76, C=80. They are outputs built during a stage; they are not all pre-existing cache hits. Only nine C questions reused an earlier cluster.

## Historical October 7 runs

| Folder | Purpose |
|---|---|
| `20261007-154533_S_DEEP_smoke` | Initial one-question smoke check |
| `20261007-154909_S_DEEP_smoke2` | Follow-up smoke check |
| `20261007-155154_S_DEEP_baseline` | 48-question DEEP, top-k 5, reuse enabled |
| `20261007-162005_S_DEEP_noreuse` | 48-question DEEP, top-k 5, reuse disabled |
| `20261007-164806_S_DEEP_noreuse_k10` | 48-question DEEP, top-k 10, reuse disabled |
| `api_clusters/` | Separate cluster export from the API workspace; not C's initial memory |

`poc/results/report.md` is the historical 48-question report. Preserve its context: five question references were subsequently corrected, and those old results were not regraded. The principal October 14 report uses the new reference snapshot and improved token accounting.

The original result ZIP and its checksum manifest are included. They preserve the pre-publication export, including original Chinese narrative documents. Use the repository's English reports for reading. Frozen code and historical logs are evidence, not a statement that every archived script or local path is the current portable interface.
