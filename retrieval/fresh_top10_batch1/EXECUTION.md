# Batch execution

The batch ran on 26 October 2026 in the existing container, under `/retrieval_fresh_top10_batch1_20261026`.

1. Freeze the 120 questions, 81 original hashes, installed source hashes, native settings, ranking prompt and driver. Create a fresh directory scan and isolated parsing cache.
2. Run each question through keyword extraction, keyword search and directory selection. Preserve up to ten files in native order. Record requests, attempts and complete candidate lists.
3. Freeze these new results. Build ranking payloads from the same files with original ranks and grading labels hidden. Run one Top-10 ranking pass, preserving empty and single-file lists.
4. Export both groups. Apply shared source-support labels, reusing 402 compatible decisions and checking 72 new or upgraded associations. Resolve two unmatched-quotation cases against saved source text without changing their negative labels.
5. Score the 98 single-document cases and report the other 22 separately. Verify request identities, source hashes, candidate equality, per-query Top-10 invariance and scoring completeness. Publish the raw records with the comparison.

## Recovery records

The first retrieval completed before a datetime serialization error in the wrapper. The saved native result was recovered without another request. Original code and the serialization-only change are in [execution_repair](execution_repair/revision.json).

Three connection interruptions required resumes. Checkpoints preserve 41 completed retrieval results, then 96, then all 120 retrieval results plus 80 ranking results. Completed tasks were not repeated. Failed attempts remain recorded.

CONS-08 exhausted three ranking attempts and retained the original ordering. Its supporting source remains fifth. This fallback is included in all reported measures.

The native legacy DOC parsing limitation was retained. The warmup's binary-match output is not readable document text. No parser or directory-budget change was introduced.

## Records

- [Frozen plan](PLAN.md), [initial freeze](freeze.json), [metadata freeze](scan_freeze.json) and [candidate freeze](rerank_freeze.json).
- [Completion](retrieval_complete.json), [source-check completion](support_complete.json) and [scoring inputs](scoring_freeze.json).
- [Report](reports/REPORT.md), [validation](reports/validation.json) and [artifact hashes](artifact_manifest.json).

Parsing caches and query state remain in the local container. Exported records exclude credentials and those caches. Source-check requests and downtime are excluded from retrieval and ranking timing measures.
