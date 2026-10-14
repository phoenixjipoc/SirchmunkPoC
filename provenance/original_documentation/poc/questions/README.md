# 评测题库

2026-10-14 已完成 120 题独立 AI 核验：109 题原答案获支持，11 题经原文复核修正。三名验证代理各盲答 40 题，再与原答案比对；不是人工认证。

- `questions.csv`：当前主表。
- `questions_verified.csv`：本轮可用于评测的 120 题快照。
- `verification/verification_report.md`：核验方法、修正清单、限制及对旧实验的影响。
- `verification/audit_20261014/`：原始版本、冻结盲答、逐题证据和裁定。
- `draft_*.jsonl`：原始出题草稿，未修改。批准修正单独保存在 `verification/approved_corrections.jsonl`，构建时覆盖对应字段。

`gold_answer` 是当前参考答案；`verify_answer` 保留最初独立盲答，可能含后续发现并记录的错误。`verify_status` 为 `verified` 或 `corrected`，`verify_note` 提供差异及接受标准。`review_status` 仍为 `auto_drafted`，保留原人工审核字段的含义。

重建主表：`python poc/questions/build_questions.py`。重新发布本轮核验快照：`python poc/questions/verification/finalize_verification.py`。不要覆盖本轮 `verification/blind_*.jsonl`；新的盲测应另存为新一轮审计输入。

原 48 题实验没有重新运行或评分。后续全量 DEEP 评测应使用当前版本；题库核验通过不能替代检索与回答效果评测。
