# Top-five and top-ten reranking

One fixed-candidate comparison on 120 questions and 81 original documents. RR5 reorders the first five baseline candidates; RR10 reorders the first ten. Both retain at most ten references. Inputs use file information and previews capped at 800 characters per document.

The primary measures use 98 single-document questions. Combined-source, thematic and negative questions are reported separately. No final answers or knowledge clusters are produced.

Top-1: baseline 52.04% (51/98), RR5 75.51% (74/98), RR10 80.61% (79/98). Both arms retain Top-10 at 81.63% (80/98). See the [report](reports/REPORT.md) and [all 360 scores](reports/questions.csv). RR5 includes one recorded technical fallback.

- [Plan](PLAN.md): scope, controls and scoring.
- `inputs/`, `baseline/`, `freeze.json`: immutable payloads and original retrieval records.
- `runs/RR5/`, `runs/RR10/`: requests, attempts and completed results.
- `scoring_inputs/`, `review_inputs/`, `support_reviews/`: reused decisions and new source checks.
- `reports/`: scores, paired changes, validation and summary.
- `execution_logs/`: process output.

## Execution

For a fresh experiment, create a sibling directory under `retrieval/` containing the source scripts, prompt preparation code and PLAN.md. Exclude existing freezes, results and call records. Preparation copies the original inputs and refuses to overwrite a frozen experiment. The container requires the original corpus at `/mnt/docs/S` and the unchanged installed package. Runtime credentials remain in the existing environment.

```bash
python prepare.py
python run.py --smoke
python run.py
```

The first question has a single candidate, so the smoke step checks transport, runtime identity and the skip path. The first nontrivial full-run tasks exercise permutation validation. Completed tasks are retained on resume.

After collection, prepare source checks on the host. Run check_support.py in the container only after ranking completes, then collect its records. Resolve any uncertain evidence against the original sources before publishing scores.

```bash
python prepare_reviews.py
python check_support.py --root /path/to/container/experiment
python analyze.py
python write_report.py
python validate.py
```

The request client and source-check worker are copied from the existing retrieval experiment. The ranking runner adds one permitted phase without modifying the original client. Settings and request records identify the exact runtime.
