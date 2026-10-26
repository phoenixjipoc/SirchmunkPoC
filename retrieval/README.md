# Document retrieval baseline

One pass over 120 verified questions and 81 raw documents. Each query returns up to ten files. There are no final answers, evidence summaries or knowledge clusters.

- [Plan and scoring rules](PLAN.md)
- [Report](reports/basic120/REPORT.md)
- [Per-question scores](reports/basic120/questions.csv)
- [Every returned reference](reports/basic120/references.csv)
- [Similar-question pairs](reports/basic120/pairs.csv)
- [Cross-document coverage](reports/basic120/cross_document.csv)
- [Unanswerable cases](reports/basic120/unanswerable.csv)
- [Follow-up using the same 120 questions](followup120/README.md): repeatability, directory coverage and parsing.

## Files

`inputs/` freezes questions, source identities, acceptance rules and settings. Only questions, corpus hashes and settings enter the retrieval process. `results/basic120/` contains runtime checks, call records and the ordered results. `review_inputs/` and `support_reviews/` belong to separate source checking. `reports/basic120/` contains the final scores and interpretation.

`attempts/` preserves superseded starts and the earlier parser preflight. None contributes to baseline scoring. `source_snapshot/` and the source hashes document the installed retrieval implementation.

## Reproduce

Use the existing container with the original documents at `/mnt/docs/S`. Required credentials stay in the container environment. The launcher explicitly applies the runtime identifier from `inputs/config.json` and checks it on every call.

1. Install host dependencies from the repository's single `requirements.txt`.
2. Run `python retrieval/freeze.py` to recreate the input snapshot.
3. Set a fresh `container_root` in `retrieval/inputs/config.json` for a new independent run. Do not overwrite an existing result directory. Archive the local `results/basic120/` before collecting another run.
4. Run `python retrieval/launch.py`. It runs offline guard checks, verifies source hashes, warms parsing caches, confirms the endpoint and executes all 120 questions sequentially.
5. Run `python retrieval/launch_review.py --root /your_fresh_support_path` after collecting the results. It builds jobs for unlisted documents, runs the source checks and copies decisions back. `watch_support.py` performs the same checks incrementally while retrieval is running.
6. Collect `support_reviews/`, resolve documented ambiguities against the sources, and run `python retrieval/score.py`.

The ordered files come from the installed DEEP discovery methods. Keyword hits take precedence over directory suggestions. The directory path randomly samples twenty files, so a fixed seed and one pass do not establish stability. Top-5 and Top-10 are prefixes of the same ten-file result, not separate budget experiments.

Scoring uses all 98 single-document questions as its main denominator. The twelve source-combination questions, thematic synthesis and nine negatives have separate outputs. Missing assessments remain explicit; no unknown is silently converted to a correct result.
