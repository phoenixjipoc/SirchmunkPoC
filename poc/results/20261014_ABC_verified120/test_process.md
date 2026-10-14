# A -> B -> C execution process

All stages use 120 verified questions, 81 original files, DEEP mode and serial questions. A=k10/reuse off; B=k5/reuse off; C=k10/reuse on at 0.85. Each stage starts with an empty knowledge store; the parsed-text cache is shared.

Search input contains only IDs/questions. Frozen references and acceptance criteria are used later for grading. Primary and secondary model judging share the search model configuration; coordinating review is separately recorded.

The legacy DOC parser issue was retained throughout all stages. A JSONL export failure was repaired without rerunning search. Connection retries and serialization recoveries remain in the metrics and logs.

Events below preserve the original order and timestamps. Historical command paths refer to the original workspace; use the reproduction guide for the new checkout. The first exporter-repair event prematurely reported a test pass; the later `export_regression_test_passed` event explicitly corrects that record.

## Execution events

- **2026-10-14T12:51:31+08:00** `prepared`

```json
{
  "question_sha256": "84f8a790551fabc154b74f9f59e0e13dde0eff7f06b38de9eb3afb27d341fb11",
  "parser_limitations": [
    "INREV__INREV_DDQ_Fund_of_Funds_and_Multi-Managers.doc"
  ]
}
```

- **2026-10-14T12:51:31+08:00** `search_started`

```json
{
  "stage": "A",
  "command": [
    "C:\\Users\\XUJI\\AppData\\Local\\Python\\pythoncore-3.14-64\\python.exe",
    "-u",
    "C:\\Users\\XUJI\\OneDrive - Capco\\Desktop\\Sirchmunk_PoC\\poc\\run_eval.py",
    "--tier",
    "S",
    "--mode",
    "DEEP",
    "--questions",
    "C:\\Users\\XUJI\\OneDrive - Capco\\Desktop\\Sirchmunk_PoC\\poc\\results\\20261014_ABC_verified120\\inputs\\questions.csv",
    "--top-k-files",
    "10",
    "--sim-threshold",
    "0.85",
    "--output-dir",
    "C:\\Users\\XUJI\\OneDrive - Capco\\Desktop\\Sirchmunk_PoC\\poc\\results\\20261014_ABC_verified120\\A",
    "--no-reuse",
    "--run-id",
    "20261014_ABC_verified120_A"
  ]
}
```

- **Timestamp not recorded in the original event** `parser_followup`

```json
{
  "file": "INREV__INREV_DDQ_Fund_of_Funds_and_Multi-Managers.doc",
  "finding": "Partially garbled fast_extract output; 63927 chars, 240 replacement characters; rga binary match. Kept unchanged across A/B/C."
}
```

- **2026-10-14T13:29:49+08:00** `continuation_waiting_for_A`

```json
{}
```

- **2026-10-14T14:01:32+08:00** `coordinating_review_progress`

```json
{
  "stage": "A",
  "reviewed_unique": 50,
  "notes": "Reference review during search; frozen gold plus previously audited passages. No extra search-model requests."
}
```

- **2026-10-14T14:01:32+08:00** `direct_analysis_finding`

```json
{
  "stage": "A",
  "question": "CONS-16",
  "finding": "DQ direct analysis bypassed retrieval and answered inability to compare the ten named RFPs. Installed collect_doc_files default is five files, independent of top_k.",
  "source": "inputs/direct_doc_analysis_source.txt;inputs/doc_qa_collection_source.txt"
}
```

- **2026-10-14T14:09:48+08:00** `search_finished`

```json
{
  "stage": "A",
  "returncode": 0
}
```

- **2026-10-14T14:09:48+08:00** `judge_started`

```json
{
  "stage": "A",
  "command": [
    "C:\\Users\\XUJI\\AppData\\Local\\Python\\pythoncore-3.14-64\\python.exe",
    "-u",
    "C:\\Users\\XUJI\\OneDrive - Capco\\Desktop\\Sirchmunk_PoC\\poc\\judge.py",
    "C:\\Users\\XUJI\\OneDrive - Capco\\Desktop\\Sirchmunk_PoC\\poc\\results\\20261014_ABC_verified120\\A"
  ]
}
```

- **2026-10-14T14:13:19+08:00** `judge_finished`

```json
{
  "stage": "A",
  "returncode": 0
}
```

- **2026-10-14T14:13:22+08:00** `stage_failed`

```json
{
  "stage": "A",
  "error": "JSONDecodeError: Unterminated string starting at: line 1 column 333392 (char 333391)"
}
```

- **2026-10-14T14:18:32+08:00** `exporter_repaired`

```json
{
  "file": "export_clusters.py",
  "old_sha256": "25839743c846edc34d0cd8ee74b6bd340460f104f6154b2a694b21f44021a5ac",
  "new_sha256": "38bc227acfbbd2b84f31b8bef8e242390a5fcbb0c3028cc60f04dc8a0c2b550e",
  "scope": "post-processing only",
  "reason": "Fix JSONL record splitting for 30 U+2029 characters in existing evidence; ASCII escaping in full JSONL preserves decoded text. No search or judge code/data changed. Regression test passed."
}
```

- **2026-10-14T14:19:07+08:00** `export_regression_test_passed`

```json
{
  "test": "test_export_clusters.py",
  "note": "One test passed. Earlier sandbox executions were blocked by temporary-directory ACLs; the earlier repair event prematurely described the test as passed, corrected by this actual result."
}
```

- **2026-10-14T14:19:11+08:00** `judge_started`

```json
{
  "stage": "A",
  "command": [
    "C:\\Users\\XUJI\\AppData\\Local\\Python\\pythoncore-3.14-64\\python.exe",
    "-u",
    "C:\\Users\\XUJI\\OneDrive - Capco\\Desktop\\Sirchmunk_PoC\\poc\\judge.py",
    "C:\\Users\\XUJI\\OneDrive - Capco\\Desktop\\Sirchmunk_PoC\\poc\\results\\20261014_ABC_verified120\\A"
  ]
}
```

- **2026-10-14T14:19:13+08:00** `judge_finished`

```json
{
  "stage": "A",
  "returncode": 0
}
```

- **2026-10-14T14:19:16+08:00** `stage_complete`

```json
{
  "stage": "A",
  "questions": 120,
  "clusters": 82
}
```

- **2026-10-14T14:19:29+08:00** `continuation_waiting_for_A`

```json
{}
```

- **2026-10-14T14:19:29+08:00** `review_A_started`

```json
{
  "command": [
    "C:\\Users\\XUJI\\AppData\\Local\\Python\\pythoncore-3.14-64\\python.exe",
    "-u",
    "C:\\Users\\XUJI\\OneDrive - Capco\\Desktop\\Sirchmunk_PoC\\poc\\review_campaign_stage.py",
    "C:\\Users\\XUJI\\OneDrive - Capco\\Desktop\\Sirchmunk_PoC\\poc\\results\\20261014_ABC_verified120\\A"
  ]
}
```

- **2026-10-14T14:20:14+08:00** `review_A_finished`

```json
{
  "returncode": 0
}
```

- **2026-10-14T14:20:14+08:00** `report_after_A_started`

```json
{
  "command": [
    "C:\\Users\\XUJI\\AppData\\Local\\Python\\pythoncore-3.14-64\\python.exe",
    "-u",
    "C:\\Users\\XUJI\\OneDrive - Capco\\Desktop\\Sirchmunk_PoC\\poc\\campaign_report.py",
    "C:\\Users\\XUJI\\OneDrive - Capco\\Desktop\\Sirchmunk_PoC\\poc\\results\\20261014_ABC_verified120"
  ]
}
```

- **2026-10-14T14:20:14+08:00** `report_after_A_finished`

```json
{
  "returncode": 0
}
```

- **2026-10-14T14:20:14+08:00** `stage_B_started`

```json
{
  "command": [
    "C:\\Users\\XUJI\\AppData\\Local\\Python\\pythoncore-3.14-64\\python.exe",
    "-u",
    "C:\\Users\\XUJI\\OneDrive - Capco\\Desktop\\Sirchmunk_PoC\\poc\\run_campaign.py",
    "C:\\Users\\XUJI\\OneDrive - Capco\\Desktop\\Sirchmunk_PoC\\poc\\results\\20261014_ABC_verified120",
    "--stage",
    "B"
  ]
}
```

- **2026-10-14T14:20:15+08:00** `search_started`

```json
{
  "stage": "B",
  "command": [
    "C:\\Users\\XUJI\\AppData\\Local\\Python\\pythoncore-3.14-64\\python.exe",
    "-u",
    "C:\\Users\\XUJI\\OneDrive - Capco\\Desktop\\Sirchmunk_PoC\\poc\\run_eval.py",
    "--tier",
    "S",
    "--mode",
    "DEEP",
    "--questions",
    "C:\\Users\\XUJI\\OneDrive - Capco\\Desktop\\Sirchmunk_PoC\\poc\\results\\20261014_ABC_verified120\\inputs\\questions.csv",
    "--top-k-files",
    "5",
    "--sim-threshold",
    "0.85",
    "--output-dir",
    "C:\\Users\\XUJI\\OneDrive - Capco\\Desktop\\Sirchmunk_PoC\\poc\\results\\20261014_ABC_verified120\\B",
    "--no-reuse",
    "--run-id",
    "20261014_ABC_verified120_B"
  ]
}
```

- **2026-10-14T15:38:20+08:00** `search_finished`

```json
{
  "stage": "B",
  "returncode": 0
}
```

- **2026-10-14T15:38:20+08:00** `judge_started`

```json
{
  "stage": "B",
  "command": [
    "C:\\Users\\XUJI\\AppData\\Local\\Python\\pythoncore-3.14-64\\python.exe",
    "-u",
    "C:\\Users\\XUJI\\OneDrive - Capco\\Desktop\\Sirchmunk_PoC\\poc\\judge.py",
    "C:\\Users\\XUJI\\OneDrive - Capco\\Desktop\\Sirchmunk_PoC\\poc\\results\\20261014_ABC_verified120\\B"
  ]
}
```

- **2026-10-14T15:42:06+08:00** `judge_finished`

```json
{
  "stage": "B",
  "returncode": 0
}
```

- **2026-10-14T15:42:08+08:00** `stage_complete`

```json
{
  "stage": "B",
  "questions": 120,
  "clusters": 76
}
```

- **2026-10-14T15:42:08+08:00** `stage_B_finished`

```json
{
  "returncode": 0
}
```

- **2026-10-14T15:42:08+08:00** `review_B_started`

```json
{
  "command": [
    "C:\\Users\\XUJI\\AppData\\Local\\Python\\pythoncore-3.14-64\\python.exe",
    "-u",
    "C:\\Users\\XUJI\\OneDrive - Capco\\Desktop\\Sirchmunk_PoC\\poc\\review_campaign_stage.py",
    "C:\\Users\\XUJI\\OneDrive - Capco\\Desktop\\Sirchmunk_PoC\\poc\\results\\20261014_ABC_verified120\\B"
  ]
}
```

- **2026-10-14T15:43:00+08:00** `review_B_finished`

```json
{
  "returncode": 0
}
```

- **2026-10-14T15:43:00+08:00** `report_after_B_started`

```json
{
  "command": [
    "C:\\Users\\XUJI\\AppData\\Local\\Python\\pythoncore-3.14-64\\python.exe",
    "-u",
    "C:\\Users\\XUJI\\OneDrive - Capco\\Desktop\\Sirchmunk_PoC\\poc\\campaign_report.py",
    "C:\\Users\\XUJI\\OneDrive - Capco\\Desktop\\Sirchmunk_PoC\\poc\\results\\20261014_ABC_verified120"
  ]
}
```

- **2026-10-14T15:43:01+08:00** `report_after_B_finished`

```json
{
  "returncode": 0
}
```

- **2026-10-14T15:43:01+08:00** `stage_C_started`

```json
{
  "command": [
    "C:\\Users\\XUJI\\AppData\\Local\\Python\\pythoncore-3.14-64\\python.exe",
    "-u",
    "C:\\Users\\XUJI\\OneDrive - Capco\\Desktop\\Sirchmunk_PoC\\poc\\run_campaign.py",
    "C:\\Users\\XUJI\\OneDrive - Capco\\Desktop\\Sirchmunk_PoC\\poc\\results\\20261014_ABC_verified120",
    "--stage",
    "C"
  ]
}
```

- **2026-10-14T15:43:01+08:00** `search_started`

```json
{
  "stage": "C",
  "command": [
    "C:\\Users\\XUJI\\AppData\\Local\\Python\\pythoncore-3.14-64\\python.exe",
    "-u",
    "C:\\Users\\XUJI\\OneDrive - Capco\\Desktop\\Sirchmunk_PoC\\poc\\run_eval.py",
    "--tier",
    "S",
    "--mode",
    "DEEP",
    "--questions",
    "C:\\Users\\XUJI\\OneDrive - Capco\\Desktop\\Sirchmunk_PoC\\poc\\results\\20261014_ABC_verified120\\inputs\\questions.csv",
    "--top-k-files",
    "10",
    "--sim-threshold",
    "0.85",
    "--output-dir",
    "C:\\Users\\XUJI\\OneDrive - Capco\\Desktop\\Sirchmunk_PoC\\poc\\results\\20261014_ABC_verified120\\C",
    "--run-id",
    "20261014_ABC_verified120_C"
  ]
}
```

- **2026-10-14T16:05:16+08:00** `recovered_search_connection_error`

```json
{
  "stage": "C",
  "id": "SVC-03",
  "latency_s": 137.83,
  "llm_calls": 93,
  "llm_failed_calls": 1,
  "total_tokens": 148219,
  "final_error": null,
  "finding": "knowledge_base.build() encountered Connection error, triggering automatic phase retry; final answer returned successfully. No record removed or manually rerun."
}
```

- **2026-10-14T16:39:09+08:00** `reuse_case_verified`

```json
{
  "stage": "C",
  "question": "CONS-07",
  "source_question": "CONS-06",
  "cluster": "Ca3d531d9a4",
  "finding": "Wrong retirement system and client thresholds; outside preselected pairs."
}
```

- **2026-10-14T16:46:31+08:00** `postprocessing_record_parser_hardened`

```json
{
  "files": [
    "campaign_report.py",
    "review_campaign_stage.py",
    "validate_campaign.py"
  ],
  "note": "Read JSONL records using LF delimiters rather than Unicode splitlines, consistent with the repaired exporter. No search, reference or grading policy changes."
}
```

- **2026-10-14T17:02:29+08:00** `search_finished`

```json
{
  "stage": "C",
  "returncode": 0
}
```

- **2026-10-14T17:02:29+08:00** `judge_started`

```json
{
  "stage": "C",
  "command": [
    "C:\\Users\\XUJI\\AppData\\Local\\Python\\pythoncore-3.14-64\\python.exe",
    "-u",
    "C:\\Users\\XUJI\\OneDrive - Capco\\Desktop\\Sirchmunk_PoC\\poc\\judge.py",
    "C:\\Users\\XUJI\\OneDrive - Capco\\Desktop\\Sirchmunk_PoC\\poc\\results\\20261014_ABC_verified120\\C"
  ]
}
```

- **2026-10-14T17:06:11+08:00** `judge_finished`

```json
{
  "stage": "C",
  "returncode": 0
}
```

- **2026-10-14T17:06:15+08:00** `stage_complete`

```json
{
  "stage": "C",
  "questions": 120,
  "clusters": 80
}
```

- **2026-10-14T17:06:15+08:00** `stage_C_finished`

```json
{
  "returncode": 0
}
```

- **2026-10-14T17:06:15+08:00** `review_C_started`

```json
{
  "command": [
    "C:\\Users\\XUJI\\AppData\\Local\\Python\\pythoncore-3.14-64\\python.exe",
    "-u",
    "C:\\Users\\XUJI\\OneDrive - Capco\\Desktop\\Sirchmunk_PoC\\poc\\review_campaign_stage.py",
    "C:\\Users\\XUJI\\OneDrive - Capco\\Desktop\\Sirchmunk_PoC\\poc\\results\\20261014_ABC_verified120\\C"
  ]
}
```

- **2026-10-14T17:07:10+08:00** `review_C_finished`

```json
{
  "returncode": 0
}
```

- **2026-10-14T17:07:10+08:00** `report_after_C_started`

```json
{
  "command": [
    "C:\\Users\\XUJI\\AppData\\Local\\Python\\pythoncore-3.14-64\\python.exe",
    "-u",
    "C:\\Users\\XUJI\\OneDrive - Capco\\Desktop\\Sirchmunk_PoC\\poc\\campaign_report.py",
    "C:\\Users\\XUJI\\OneDrive - Capco\\Desktop\\Sirchmunk_PoC\\poc\\results\\20261014_ABC_verified120"
  ]
}
```

- **2026-10-14T17:07:11+08:00** `report_after_C_finished`

```json
{
  "returncode": 0
}
```

- **2026-10-14T17:07:11+08:00** `all_stages_exported_pending_coordinator_disagreements`

```json
{}
```

- **2026-10-14T17:08:47+08:00** `coordinator_adjudication_complete`

```json
{
  "stage": "C",
  "disagreements_resolved": [
    "SVC-21",
    "DDQ-02"
  ],
  "note": "Original primary/secondary records preserved; final decisions recorded separately."
}
```

- **2026-10-14T17:12:01+08:00** `all_tests_reviews_exports_complete`

```json
{
  "records": 360,
  "required_reviews_resolved": 190,
  "clusters_exported": 238,
  "validation": "validation.json",
  "final_correct": {
    "A": 74,
    "B": 68,
    "C": 75
  },
  "note": "All planned A/B/C evaluations and review disagreements resolved. No extra experiments launched."
}
```

## Completion

360 search records, all 190 required review records resolved, and 238 clusters exported. See `validation.json` for original data-integrity checks. Publication/translation checks are recorded separately in the repository provenance directory.
