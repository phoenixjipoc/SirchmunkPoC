# Fresh Top-10 retrieval and reranking

One new batch of 120 questions against 81 original documents. Baseline is the fresh retrieval result from this batch; RR10 reorders that result. Historical retrieval candidates are excluded.

The [plan](PLAN.md) fixes scope and controls. The [report](reports/REPORT.md) compares first-document support, candidate coverage, similar questions and cost. All 240 scored lists are in [questions.csv](reports/questions.csv).

The [execution record](EXECUTION.md) describes the completed stages and recoveries. [Artifact hashes](artifact_manifest.json) cover the published files.

- `inputs/`: questions, original hashes, new scan and ranking payloads.
- `runs/Baseline/`: fresh keyword/directory requests, attempts and ordered results.
- `baseline/`: exact copies of this batch's retrieval results used by RR10.
- `runs/RR10/`: reranking requests, attempts and ordered results.
- `results/basic120/`: native preparation and intermediate result records.
- `execution_repair/`: serialization fix, original code and preserved first result.
- `scoring_inputs/`, `review_inputs/`, `support_reviews/`: shared labels and source checks.
- `reports/`: paired measures and validation.

## Reproduction

Run the preserved driver in an isolated container directory with the same original corpus and package. Credentials remain in the existing environment. The driver retains completed tasks when resumed. For a new campaign, start with source/configuration files and no prior result folders, and create new freezes; do not overwrite published records. Preserve the documented serialization fix when preparing a new directory.

```bash
python run_batch.py --root /path/to/experiment
```

Collect completed records before preparing source checks on the host. Source checks run afterward in the container. Collect and adjudicate their records before reporting.

```bash
python prepare_reviews.py
python check_support.py --root /path/to/experiment
python analyze.py
python write_report.py
python validate.py
```

Request identity, original hashes, fresh-candidate provenance and paired score invariants are checked offline. Parsing caches and query state remain local to the run and are excluded from publication.
