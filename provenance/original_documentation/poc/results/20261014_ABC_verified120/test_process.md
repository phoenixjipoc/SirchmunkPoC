# A → B → C 测试过程

全部使用核验后的 120 题、81 份 raw 文档、DEEP、串行请求。

|阶段|top_k|知识簇复用|
|---|---:|---|
|A|10|关闭|
|B|5|关闭|
|C|10|开启，阈值 0.85|

每轮空知识簇起步，保持题序、模型与解析缓存条件相同。C 只复用本轮前题产生的簇。

评分采用冻结参考答案及核验接受标准；错误、拒答与运行异常分开。来源覆盖率不等于答案得到支持。
搜索模型与初评模型使用同一已配置端点，存在同模型评分偏差；后续复核另行记录。
单次运行仍有模型与采样随机性，对照差异不作为统计显著性的证明。费用以 token 用量记录，不推测金额。

## 执行记录

- 2026-10-14T12:51:31+08:00 `prepared`：{"question_sha256": "84f8a790551fabc154b74f9f59e0e13dde0eff7f06b38de9eb3afb27d341fb11", "parser_limitations": ["INREV__INREV_DDQ_Fund_of_Funds_and_Multi-Managers.doc"]}

- 2026-10-14T12:51:31+08:00 `search_started`：{"stage": "A", "command": ["C:\\Users\\XUJI\\AppData\\Local\\Python\\pythoncore-3.14-64\\python.exe", "-u", "C:\\Users\\XUJI\\OneDrive - Capco\\Desktop\\Sirchmunk_PoC\\poc\\run_eval.py", "--tier", "S", "--mode", "DEEP", "--questions", "C:\\Users\\XUJI\\OneDrive - Capco\\Desktop\\Sirchmunk_PoC\\poc\\results\\20261014_ABC_verified120\\inputs\\questions.csv", "--top-k-files", "10", "--sim-threshold", "0.85", "--output-dir", "C:\\Users\\XUJI\\OneDrive - Capco\\Desktop\\Sirchmunk_PoC\\poc\\results\\20261014_ABC_verified120\\A", "--no-reuse", "--run-id", "20261014_ABC_verified120_A"]}

- 解析复核：INREV 旧 DOC 抽取文本有大量乱码；三轮均保留同一原始文件和运行时，将其列为解析限制。详见 parser_followup.json。

- 2026-10-14T13:29:49+08:00 `continuation_waiting_for_A`：{}

- 2026-10-14T14:01:32+08:00 `coordinating_review_progress`：{"stage": "A", "reviewed_unique": 50, "notes": "Reference review during search; frozen gold plus previously audited passages. No extra search-model requests."}

- 2026-10-14T14:01:32+08:00 `direct_analysis_finding`：{"stage": "A", "question": "CONS-16", "finding": "DQ direct analysis bypassed retrieval and answered inability to compare the ten named RFPs. Installed collect_doc_files default is five files, independent of top_k.", "source": "inputs/direct_doc_analysis_source.txt;inputs/doc_qa_collection_source.txt"}

- 2026-10-14T14:09:48+08:00 `search_finished`：{"stage": "A", "returncode": 0}

- 2026-10-14T14:09:48+08:00 `judge_started`：{"stage": "A", "command": ["C:\\Users\\XUJI\\AppData\\Local\\Python\\pythoncore-3.14-64\\python.exe", "-u", "C:\\Users\\XUJI\\OneDrive - Capco\\Desktop\\Sirchmunk_PoC\\poc\\judge.py", "C:\\Users\\XUJI\\OneDrive - Capco\\Desktop\\Sirchmunk_PoC\\poc\\results\\20261014_ABC_verified120\\A"]}

- 2026-10-14T14:13:19+08:00 `judge_finished`：{"stage": "A", "returncode": 0}

- 2026-10-14T14:13:22+08:00 `stage_failed`：{"stage": "A", "error": "JSONDecodeError: Unterminated string starting at: line 1 column 333392 (char 333391)"}

- 2026-10-14T14:18:32+08:00 `exporter_repaired`：{"file": "export_clusters.py", "old_sha256": "25839743c846edc34d0cd8ee74b6bd340460f104f6154b2a694b21f44021a5ac", "new_sha256": "38bc227acfbbd2b84f31b8bef8e242390a5fcbb0c3028cc60f04dc8a0c2b550e", "scope": "post-processing only", "reason": "Fix JSONL record splitting for 30 U+2029 characters in existing evidence; ASCII escaping in full JSONL preserves decoded text. No search or judge code/data changed. Regression test passed."}

- 2026-10-14T14:19:07+08:00 `export_regression_test_passed`：{"test": "test_export_clusters.py", "note": "One test passed. Earlier sandbox executions were blocked by temporary-directory ACLs; the earlier repair event prematurely described the test as passed, corrected by this actual result."}

- 2026-10-14T14:19:11+08:00 `judge_started`：{"stage": "A", "command": ["C:\\Users\\XUJI\\AppData\\Local\\Python\\pythoncore-3.14-64\\python.exe", "-u", "C:\\Users\\XUJI\\OneDrive - Capco\\Desktop\\Sirchmunk_PoC\\poc\\judge.py", "C:\\Users\\XUJI\\OneDrive - Capco\\Desktop\\Sirchmunk_PoC\\poc\\results\\20261014_ABC_verified120\\A"]}

- 2026-10-14T14:19:13+08:00 `judge_finished`：{"stage": "A", "returncode": 0}

- 2026-10-14T14:19:16+08:00 `stage_complete`：{"stage": "A", "questions": 120, "clusters": 82}

- 2026-10-14T14:19:29+08:00 `continuation_waiting_for_A`：{}

- 2026-10-14T14:19:29+08:00 `review_A_started`：{"command": ["C:\\Users\\XUJI\\AppData\\Local\\Python\\pythoncore-3.14-64\\python.exe", "-u", "C:\\Users\\XUJI\\OneDrive - Capco\\Desktop\\Sirchmunk_PoC\\poc\\review_campaign_stage.py", "C:\\Users\\XUJI\\OneDrive - Capco\\Desktop\\Sirchmunk_PoC\\poc\\results\\20261014_ABC_verified120\\A"]}

- 2026-10-14T14:20:14+08:00 `review_A_finished`：{"returncode": 0}

- 2026-10-14T14:20:14+08:00 `report_after_A_started`：{"command": ["C:\\Users\\XUJI\\AppData\\Local\\Python\\pythoncore-3.14-64\\python.exe", "-u", "C:\\Users\\XUJI\\OneDrive - Capco\\Desktop\\Sirchmunk_PoC\\poc\\campaign_report.py", "C:\\Users\\XUJI\\OneDrive - Capco\\Desktop\\Sirchmunk_PoC\\poc\\results\\20261014_ABC_verified120"]}

- 2026-10-14T14:20:14+08:00 `report_after_A_finished`：{"returncode": 0}

- 2026-10-14T14:20:14+08:00 `stage_B_started`：{"command": ["C:\\Users\\XUJI\\AppData\\Local\\Python\\pythoncore-3.14-64\\python.exe", "-u", "C:\\Users\\XUJI\\OneDrive - Capco\\Desktop\\Sirchmunk_PoC\\poc\\run_campaign.py", "C:\\Users\\XUJI\\OneDrive - Capco\\Desktop\\Sirchmunk_PoC\\poc\\results\\20261014_ABC_verified120", "--stage", "B"]}

- 2026-10-14T14:20:15+08:00 `search_started`：{"stage": "B", "command": ["C:\\Users\\XUJI\\AppData\\Local\\Python\\pythoncore-3.14-64\\python.exe", "-u", "C:\\Users\\XUJI\\OneDrive - Capco\\Desktop\\Sirchmunk_PoC\\poc\\run_eval.py", "--tier", "S", "--mode", "DEEP", "--questions", "C:\\Users\\XUJI\\OneDrive - Capco\\Desktop\\Sirchmunk_PoC\\poc\\results\\20261014_ABC_verified120\\inputs\\questions.csv", "--top-k-files", "5", "--sim-threshold", "0.85", "--output-dir", "C:\\Users\\XUJI\\OneDrive - Capco\\Desktop\\Sirchmunk_PoC\\poc\\results\\20261014_ABC_verified120\\B", "--no-reuse", "--run-id", "20261014_ABC_verified120_B"]}

- 2026-10-14T15:38:20+08:00 `search_finished`：{"stage": "B", "returncode": 0}

- 2026-10-14T15:38:20+08:00 `judge_started`：{"stage": "B", "command": ["C:\\Users\\XUJI\\AppData\\Local\\Python\\pythoncore-3.14-64\\python.exe", "-u", "C:\\Users\\XUJI\\OneDrive - Capco\\Desktop\\Sirchmunk_PoC\\poc\\judge.py", "C:\\Users\\XUJI\\OneDrive - Capco\\Desktop\\Sirchmunk_PoC\\poc\\results\\20261014_ABC_verified120\\B"]}

- 2026-10-14T15:42:06+08:00 `judge_finished`：{"stage": "B", "returncode": 0}

- 2026-10-14T15:42:08+08:00 `stage_complete`：{"stage": "B", "questions": 120, "clusters": 76}

- 2026-10-14T15:42:08+08:00 `stage_B_finished`：{"returncode": 0}

- 2026-10-14T15:42:08+08:00 `review_B_started`：{"command": ["C:\\Users\\XUJI\\AppData\\Local\\Python\\pythoncore-3.14-64\\python.exe", "-u", "C:\\Users\\XUJI\\OneDrive - Capco\\Desktop\\Sirchmunk_PoC\\poc\\review_campaign_stage.py", "C:\\Users\\XUJI\\OneDrive - Capco\\Desktop\\Sirchmunk_PoC\\poc\\results\\20261014_ABC_verified120\\B"]}

- 2026-10-14T15:43:00+08:00 `review_B_finished`：{"returncode": 0}

- 2026-10-14T15:43:00+08:00 `report_after_B_started`：{"command": ["C:\\Users\\XUJI\\AppData\\Local\\Python\\pythoncore-3.14-64\\python.exe", "-u", "C:\\Users\\XUJI\\OneDrive - Capco\\Desktop\\Sirchmunk_PoC\\poc\\campaign_report.py", "C:\\Users\\XUJI\\OneDrive - Capco\\Desktop\\Sirchmunk_PoC\\poc\\results\\20261014_ABC_verified120"]}

- 2026-10-14T15:43:01+08:00 `report_after_B_finished`：{"returncode": 0}

- 2026-10-14T15:43:01+08:00 `stage_C_started`：{"command": ["C:\\Users\\XUJI\\AppData\\Local\\Python\\pythoncore-3.14-64\\python.exe", "-u", "C:\\Users\\XUJI\\OneDrive - Capco\\Desktop\\Sirchmunk_PoC\\poc\\run_campaign.py", "C:\\Users\\XUJI\\OneDrive - Capco\\Desktop\\Sirchmunk_PoC\\poc\\results\\20261014_ABC_verified120", "--stage", "C"]}

- 2026-10-14T15:43:01+08:00 `search_started`：{"stage": "C", "command": ["C:\\Users\\XUJI\\AppData\\Local\\Python\\pythoncore-3.14-64\\python.exe", "-u", "C:\\Users\\XUJI\\OneDrive - Capco\\Desktop\\Sirchmunk_PoC\\poc\\run_eval.py", "--tier", "S", "--mode", "DEEP", "--questions", "C:\\Users\\XUJI\\OneDrive - Capco\\Desktop\\Sirchmunk_PoC\\poc\\results\\20261014_ABC_verified120\\inputs\\questions.csv", "--top-k-files", "10", "--sim-threshold", "0.85", "--output-dir", "C:\\Users\\XUJI\\OneDrive - Capco\\Desktop\\Sirchmunk_PoC\\poc\\results\\20261014_ABC_verified120\\C", "--run-id", "20261014_ABC_verified120_C"]}

- 2026-10-14T16:05:16+08:00 `recovered_search_connection_error`：{"stage": "C", "id": "SVC-03", "latency_s": 137.83, "llm_calls": 93, "llm_failed_calls": 1, "total_tokens": 148219, "final_error": null, "finding": "knowledge_base.build() encountered Connection error, triggering automatic phase retry; final answer returned successfully. No record removed or manually rerun."}

- 2026-10-14T16:39:09+08:00 `reuse_case_verified`：{"stage": "C", "question": "CONS-07", "source_question": "CONS-06", "cluster": "Ca3d531d9a4", "finding": "Wrong retirement system and client thresholds; outside preselected pairs."}

- 2026-10-14T16:46:31+08:00 `postprocessing_record_parser_hardened`：{"files": ["campaign_report.py", "review_campaign_stage.py", "validate_campaign.py"], "note": "Read JSONL records using LF delimiters rather than Unicode splitlines, consistent with the repaired exporter. No search, reference or grading policy changes."}

- 2026-10-14T17:02:29+08:00 `search_finished`：{"stage": "C", "returncode": 0}

- 2026-10-14T17:02:29+08:00 `judge_started`：{"stage": "C", "command": ["C:\\Users\\XUJI\\AppData\\Local\\Python\\pythoncore-3.14-64\\python.exe", "-u", "C:\\Users\\XUJI\\OneDrive - Capco\\Desktop\\Sirchmunk_PoC\\poc\\judge.py", "C:\\Users\\XUJI\\OneDrive - Capco\\Desktop\\Sirchmunk_PoC\\poc\\results\\20261014_ABC_verified120\\C"]}

- 2026-10-14T17:06:11+08:00 `judge_finished`：{"stage": "C", "returncode": 0}

- 2026-10-14T17:06:15+08:00 `stage_complete`：{"stage": "C", "questions": 120, "clusters": 80}

- 2026-10-14T17:06:15+08:00 `stage_C_finished`：{"returncode": 0}

- 2026-10-14T17:06:15+08:00 `review_C_started`：{"command": ["C:\\Users\\XUJI\\AppData\\Local\\Python\\pythoncore-3.14-64\\python.exe", "-u", "C:\\Users\\XUJI\\OneDrive - Capco\\Desktop\\Sirchmunk_PoC\\poc\\review_campaign_stage.py", "C:\\Users\\XUJI\\OneDrive - Capco\\Desktop\\Sirchmunk_PoC\\poc\\results\\20261014_ABC_verified120\\C"]}

- 2026-10-14T17:07:10+08:00 `review_C_finished`：{"returncode": 0}

- 2026-10-14T17:07:10+08:00 `report_after_C_started`：{"command": ["C:\\Users\\XUJI\\AppData\\Local\\Python\\pythoncore-3.14-64\\python.exe", "-u", "C:\\Users\\XUJI\\OneDrive - Capco\\Desktop\\Sirchmunk_PoC\\poc\\campaign_report.py", "C:\\Users\\XUJI\\OneDrive - Capco\\Desktop\\Sirchmunk_PoC\\poc\\results\\20261014_ABC_verified120"]}

- 2026-10-14T17:07:11+08:00 `report_after_C_finished`：{"returncode": 0}

- 2026-10-14T17:07:11+08:00 `all_stages_exported_pending_coordinator_disagreements`：{}

- 2026-10-14T17:08:47+08:00 `coordinator_adjudication_complete`：{"stage": "C", "disagreements_resolved": ["SVC-21", "DDQ-02"], "note": "Original primary/secondary records preserved; final decisions recorded separately."}

- 2026-10-14T17:12:01+08:00 `all_tests_reviews_exports_complete`：{"records": 360, "required_reviews_resolved": 190, "clusters_exported": 238, "validation": "validation.json", "final_correct": {"A": 74, "B": 68, "C": 75}, "note": "All planned A/B/C evaluations and review disagreements resolved. No extra experiments launched."}
