# Retrieval follow-up: the same 120 questions

Keep the original 120 questions, 81 raw documents and verified acceptance rules unchanged. The completed baseline remains immutable. No final answers or knowledge clusters are produced.

## Comparisons

- R1: the existing baseline, seed 17011, native keyword-first order and twenty randomly selected directory candidates.
- R2 and R3: two full 120-question repeats of the same implementation, seeds 17012 and 17013. Report mean, range and per-question agreement across R1/R2/R3. These are repeated observations, not 360 independent questions.
- S: rerank exactly the first ten files returned by R1 using only the question and frozen directory metadata/previews. Present candidates in filename order to avoid carrying the original rank into the request. Return a permutation of file identifiers, with no proposed answer. No candidate may be added or removed. Compare S with R1; Hit@10 must be unchanged for valid permutations.
- D: reuse R1 keyword results and the same directory snapshot, but evaluate all 81 directory candidates instead of twenty. Keep the installed relevance prompt, high-relevance filter, keyword-first merge and ten-file limit. Compare D with R1. This is a conditional directory-stage comparison, not a new full search run or a change to the keyword path.
- K and T: replay R1 keyword-only and directory-only lists without additional requests. Treat these as diagnostic source-path views, not independent full runs.
- P: validate a repaired legacy DOC parser and replay the same 120 frozen keyword searches with that parser where feasible. Preserve originals, adapter provenance, failed attempts and before/after output; isolate parsing from the other comparisons.

Freeze prompts, settings, inputs and code before the first new retrieval request. Do not tune them against these scores. All 120 questions are already exposed, so this follow-up is descriptive regression testing, not an unseen holdout evaluation.

## Measurement

The primary set remains 98 single-document questions. Report Document Hit@1/5/10, MRR@10, question-type breakdowns and equal-weight document averages. A valid document contains all mandatory facts for the correct issuer, version and conditions. The twelve required-source combinations and one thematic question remain separate. Nine negative cases report suggestions only; no refusal accuracy is inferred.

Record the first correct rank, candidate presence, first-position confusion with an opposite paired source, and failures due to empty retrieval, absent candidates, cutoff or ordering. Do not infer a parser failure or wrong-version error solely from a miss. Compare paired outcomes on identical question IDs. For S/D, report gains and losses against R1; no causal model comparison is claimed.

Reuse the completed source audit and existing source checks when the question, source hash and acceptance rules match. Review newly returned unlisted sources against the full original-derived text. A newly first-ranked unlisted source needs two separate checks, even if it had only one lower-rank check before. Unresolved classifications remain explicit; report bounds rather than silently treating them as negatives. Preserve page/section locators and verbatim source anchors separately from search inputs.

## Execution

Use one active search process and the shared parsed-text cache. Run no scoring requests concurrently with timed retrieval. Validate every outbound and returned runtime identifier. Retry only technical failures, at most three attempts, preserving all attempts; a model mismatch stops the campaign. Never retry a completed semantic miss. Save preparation time, retrieval time, scoring time, request usage and retry overhead separately. R1 timing includes concurrent source checks and is not an isolated speed baseline. S/D timings are stage-only costs.

Keep the new scripts, immutable inputs, raw results, support decisions, validation and English reports in this folder. Publish them on the existing retrieval branch when complete.
