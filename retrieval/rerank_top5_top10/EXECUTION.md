# Execution record

The campaign ran on October 26, 2026 (UTC), in the existing container. Source revision and frozen hashes are recorded in freeze.json. The installed source and all 81 original document hashes matched before execution.

## Sequence

1. Prepare 240 fixed payloads from the 120 R1 results. Use the same fields and 800-character preview limit in both arms.
2. Verify runtime identity. The first question has one candidate; its smoke result is retained in the campaign.
3. Run both arms serially, alternating their order for successive questions. Validate every response as an exact permutation.
4. At RR5 XD-01, three connection failures exhausted the task limit. Preserve the original order. A failed recovery preflight stopped subsequent tasks.
5. Verify the connection again and resume unfinished tasks. Preserve all 97 previously completed results byte for byte; recovery_1.json records their hashes. Prompts and settings did not change.
6. Complete all 240 tasks. Collect 185 successful rankings, 54 empty/single-candidate skips and one technical fallback.
7. Reuse 459 compatible unlisted-source decisions and perform fourteen missing second checks against full source text. All fourteen remained unsupported; no unresolved decisions or quotation mismatches remained.
8. Score all three groups with identical labels, validate the artifacts and publish the English report.

## Records and usage

- Ranking: RR5 95 requests, including three failed attempts; RR10 93 requests. Reported usage totals 263,679 tokens.
- Preflight: four requests, including the failed recovery check; 45 reported tokens.
- Source checks: fourteen requests and 326,889 tokens, separate from ranking.
- No additional retrieval requests or completed-task reruns were made.

XD-01 already had the correct document first in the baseline. Its fallback therefore remains a hit, but it is not evidence of a successful RR5 ranking request. All 98 single-document questions remain in the denominator.

The local collection initially reached the scoring script before copying had finished. Collection guards stopped it; preparation was rerun after the complete copy. This did not issue service requests or affect ranking records.

See execution_logs/, preflight_calls.jsonl, runs/, support_reviews/, recovery_1.json and reports/validation.json. Historical retrieval inputs, source decisions and results remain unchanged.
