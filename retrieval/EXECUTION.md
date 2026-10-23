# Execution record

Date: 23 October 2026. Times in raw records use UTC; the host displays UTC+8.

## Workspace and scope

A separate checkout, `SirchmunkPoC_Retrieval`, was created from main at `4f50995fa28e800788579dce61c95ee29a860240`. Its branch is `retrieval-only-gpt-6-sol`, with the existing repository as origin. The original checkout was left intact.

The initial design used two file limits with three repetitions. Six simultaneous processes exhausted container memory before a query completed. A sequential restart completed sixteen queries before the design was replaced at the user's request. Those records are under `attempts/`; none is scored here.

The accepted simplified design uses all 120 questions once and a single ten-file result list. Top-1, Top-5 and Top-10 are prefixes of that list. Document-level retrieval stops before evidence sampling or answer generation.

## Preparation

Original hashes matched the verified 81-document corpus. The initial warmup found matches in all 81 originals. A subsequent JSON-event check distinguished 80 readable-text inputs from one legacy DOC returning raw byte matches. That limitation is preserved in `parser_validation.json`; the warmup flag alone must not be interpreted as text-extraction quality. Directory metadata and parsing caches were prepared once; only those document-derived caches are shared. Query state is fresh for every question.

Only queries, corpus hashes and configuration were copied into the retrieval input folder. Standard answers and expected-source labels stay in the separate assessment folder. Installed source hashes, image digest and dependency versions are recorded alongside the outputs.

Offline checks covered incorrect or missing runtime identifiers, native candidate ordering, and serializing timestamped search logs. A live endpoint check confirmed the selected runtime using both the outbound HTTP body and raw response. Every subsequent call uses the same checks.

The first basic-run start exposed a timestamp serialization error after one completed query. Its records are archived under `attempts/basic_start_serialization/`. The logging fix changed no prompts, retrieval order or scoring rules. A clean run started in a new container directory; the final baseline uses only that run.

## Retrieval

`launch.py` invokes `basic_run.py prepare` and `basic_run.py run` in `/retrieval_basic_20261023_v2`. Questions run sequentially. Keyword search and directory selection can run concurrently within a question.

The adapter records keyword-discovered files and directory suggestions before merging them. Keyword files retain priority; duplicate paths are removed, and the first ten are returned. Directory selection retains the installed random twenty-candidate sample. No global reranking is introduced.

`results/basic120/queries/` stores each ordered result. `calls.jsonl` stores runtime identities, request identifiers, phase, usage and responses. `progress.jsonl` records completion and duration per question. `complete.json` records the terminal count and statuses.

A service connection interruption occurred after 51 complete queries. One query had a partial result and 68 could not execute. After a live endpoint check confirmed recovery, `resume.py` retried only those 69 technical failures with the frozen retrieval code, inputs and seeds. The 51 completed results were retained byte for byte. Initial records, call failures and recovery progress are retained; a semantic miss is never retried to obtain a better rank.

## Assessment

Known supporting files use the completed question/source audit. Unlisted returned documents are checked against complete original-derived text with whitespace normalized. `watch_support.py` runs in a separate directory and reads only completed retrieval outputs. It never modifies queries or rankings.

Every unlisted first result and every proposed additional supporting file receives two separate support requests. Neither sees the other verdict or the result rank. Exact quotations are checked against the supplied text. Conflicts are resolved against source passages and recorded separately; unresolved cases remain explicit.

The scorer keeps 98 single-document questions in the primary denominator. Twelve source-set questions, one thematic question and nine negatives have separate measures. Similar-pair results are a subset of the same 120 questions. Source-check calls and their usage are separate from retrieval calls.

## Publication

The final report, complete records, source checks and validation are published together on this branch. Superseded attempts remain clearly separated from the baseline. Exact counts and outcomes are in [the report](reports/basic120/REPORT.md) and [summary data](reports/basic120/summary.json).
