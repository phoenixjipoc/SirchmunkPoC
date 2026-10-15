# Reproduce and inspect

## Offline checks

The checked-in corpus and results can be inspected without Docker or credentials.

```bash
python poc/validate_campaign.py poc/results/20261014_ABC_verified120
```

The validator checks source hashes, frozen inputs, recorded answers, aggregate scores, and review completion. It refreshes the campaign's [validation record](../poc/results/20261014_ABC_verified120/validation.json), including its timestamp. English presentation tables are saved under `reports/verified120/`; original responses and scoring records remain in the campaign directory.

Harness checks:

```bash
python -m pip install -r requirements.txt
python -m unittest discover -s poc -p "test_*.py"
```

The six tests cover coverage accounting, refusal denominators, grading inputs, labels, and Unicode-safe export. They make no external service calls.

## Prepare Docker

Use a running container named `sirchmunk` with the image and service configuration recorded in [run_meta.json](../poc/results/20261014_ABC_verified120/A/run_meta.json). Set the credentials and settings named in [.env.example](../.env.example); keep secrets outside version control. The host needs Python, `requests`, and `truststore`. Optional source-audit dependencies are in `requirements-audit.txt`.

```bash
docker exec sirchmunk mkdir -p /mnt/docs
docker cp poc_docs/S sirchmunk:/mnt/docs/
```

The harness uses the container's existing SDK. Recreating the container requires copying the corpus again.

## Run a new campaign

Use a fresh directory; never overwrite the recorded campaign. New evaluations incur service usage.

```bash
python poc/campaign_preflight.py poc/results/NEW_RUN_ID
python poc/run_campaign.py poc/results/NEW_RUN_ID --stage A
python poc/continue_campaign.py poc/results/NEW_RUN_ID
```

Preflight checks hashes, parsing, credentials, and text-cache preparation. The continuation reviews A, then runs and reviews B and C. A=k10/reuse off; B=k5/off; C=k10/on. Each stage starts with empty cluster storage.

Resolve review disagreements against source evidence and append decisions to each stage's `review_decisions.jsonl`. Then run:

```bash
python poc/campaign_report.py poc/results/NEW_RUN_ID
python poc/validate_campaign.py poc/results/NEW_RUN_ID
```

The original report generator and its output are preserved as recorded. Frozen `inputs/scripts/` files are audit copies; executable entry points are under `poc/`. Input/code hashes are checked when resuming an incomplete stage with `--resume`.

The experiment exercises the Python SDK, not the HTTP API or UI. New answers, timing, usage, and grades may vary; preserve new logs and review them separately.
