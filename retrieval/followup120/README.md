# Retrieval follow-up

The same 120 questions and 81 raw documents are used throughout. The [plan](PLAN.md) defines repeated runs, directory coverage and a separate legacy parser comparison. Original results are preserved in [the baseline report](../reports/basic120/REPORT.md).

## Files

- `experiment.py`: full repeats and controlled directory runs.
- `legacy_adapter.py`, `parser_replay.py` and `parser_replay_corrected.py`: Word97 parser, retained replay routine and corrected asynchronous integration.
- `prepare_support.py` and `check_support.py`: pool source checks, reuse unchanged evidence and check new associations after retrieval.
- `analyze.py`: hit rates, reciprocal rank, repeated-run agreement, document averages and matched changes.
- `inputs`, `baseline`, `settings.json` and `freeze.json`: immutable retrieval inputs and source hashes. Scoring inputs are kept separately.
- `runs`: ordered results, attempts and request records.
- `scoring_inputs`, `review_inputs` and `support_reviews`: source anchors, support decisions and their provenance.
- `reports`: comparison outputs and validation.

## Reproduction

Use the same container and raw corpus as the [baseline reproduction guide](../README.md). Install the root requirements for host source checks. Copy this folder into a fresh container directory and install `olefile==0.47` into its `parser_dependencies` directory for the legacy adapter. The parser supports the single frozen legacy source; it is not a general Word conversion library.

Run `adapter/test_runtime.py` and `test_followup.py`. Run `experiment.py --root <directory>` with the configured runtime identifier. The final parser comparison uses `parser_replay_corrected.py`, which wraps the retained `parser_replay.py` routine. The initial routine alone did not enable the repaired parser in live search; see the [correction record](PARSER_CORRECTION.md). Runtime credentials stay in the container environment and must not be committed.

The retained supervisors reproduce this campaign's execution history: `supervise.py` completes the original stages and source checks; `complete_parser_correction.py` then archives the invalid parser comparison, runs corrected P/P0, rebuilds the reference pool, and completes additional checks. Run the corrected driver's `smoke` action before its `run` action. Completed query records are resumed, so use a separate directory when repeating the campaign from scratch.

For source checking, run `prepare_support.py` on the host, copy its jobs and source text to the container, then run `check_support.py --root <directory>`. New first-ranked associations require two checks; preserve prior decisions only when the question, criteria and source hash match. Copy results back after completion.

After resolving source-check disagreements against the retained evidence, run `analyze.py`, `diagnostics.py`, `validate.py`, then `write_report.py`. The generated report links to the full result files.

The source-check worker imports the unchanged baseline `review_support.py`; copy that file into the container's `adapter` directory. Keep the baseline raw results and the completed source audit available in their repository paths when running host analysis.

The first completed valid result is retained for each query and group. Technical failures have at most three attempts. Model mismatches stop execution. Document suggestions on negative questions are not evaluated as generated answers or refusal decisions.

Candidate-absence and cutoff diagnoses refer to the verified source list. Files outside the returned ten are not exhaustively judged. The primary hit and reciprocal-rank measures use support decisions for the returned documents.

For a deployed campaign, `python retrieval/followup120/supervise.py` continues unfinished groups, collects results, runs the parser comparison and starts separate source checks. Run only one supervisor. Network failures can resume; identity, authorization and other unexpected failures stop execution. Final source adjudication and reporting remain separate.

After that supervisor finishes, run `python retrieval/followup120/complete_parser_correction.py`. The final P/P0 outputs use fixed file-path order in both arms and record actual asynchronous invocation arguments. The first parser attempt remains in `parser_initial_invalid` and is excluded from final comparison scores.

On a resumed group, `complete.json` records the latest process segment. Use per-query records and request logs for complete usage; do not treat that segment duration as the full campaign duration.


Published groups are R1, R2, R3, D, P0 and P; K/T are diagnostic views. The [publication scope](publication_scope.json) verifies retained raw result bytes. Frozen input hashes and installed-source hashes describe execution; publication hashes identify the current scripts and documentation.
