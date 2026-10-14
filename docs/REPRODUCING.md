# Reproducing and inspecting the PoC

## Inspect the published evidence offline

The corpus and results are checked in. No Docker, credentials, or model calls are needed to read them. With Python, run from the repository root:

```bash
python tools/verify_publication.py
python tools/build_english_reports.py
```

The first command verifies the publication. The second rebuilds English presentation artifacts for the recorded campaign; it does not rerun search or grade translated answers.

For harness unit checks:

```bash
python -m pip install -r requirements.txt
python -m unittest discover -s poc -p "test_*.py"
```

These tests cover multi-source coverage, reuse citation accounting, unanswerable denominators, complete judge prompts, invalid labels, and Unicode-safe cluster export. They do not call a live model.

## Prepare a fresh evaluation environment

The original orchestration was run from Windows with Docker Desktop. The host-side scripts need Python, `requests`, and `truststore`. Source-audit tools additionally need PyMuPDF, python-docx, and olefile; installed dependency directories and Python bytecode are intentionally not vendored in this repository.

Provide an already-running container named `sirchmunk` using the recorded Sirchmunk image and a compatible model endpoint. The required container environment settings are `LLM_MODEL_NAME`, `LLM_BASE_URL`, and `LLM_API_KEY`. The reference run used `gpt-5.4`; keep credentials outside version control. `.env.example` names the settings but contains no credential.

The recorded image is:

```text
modelscope-registry.us-west-1.cr.aliyuncs.com/modelscope-repo/sirchmunk:ubuntu22.04-py312-0.0.7
sha256:d3a08d8cd3a738362ebf662ebf3dd261b63a12854c5fdb8c27fc58b95364927d
```

Copy the original files into that container:

```bash
docker exec sirchmunk mkdir -p /mnt/docs
docker cp poc_docs/S sirchmunk:/mnt/docs/
```

No automatic setup command in this repository changes your model endpoint or installs a live service. The harness uses the container's existing Sirchmunk SDK and the same raw-file location as the reference run.

## Run a new campaign, never overwrite the published run

Choose a fresh directory name; `NEW_RUN_ID` below is a placeholder. New evaluations consume model API tokens.

```bash
python poc/campaign_preflight.py poc/results/NEW_RUN_ID
python poc/run_campaign.py poc/results/NEW_RUN_ID --stage A
python poc/continue_campaign.py poc/results/NEW_RUN_ID
```

Preflight verifies raw-document hashes, parsability, credential presence without printing the credential, and rga cache preparation. A uses k10/reuse off. The continuation reviews A, then runs and reviews B (k5/off), then C (k10/on), serially. It generates provisional aggregate reports after each stage. The archived generator's output language is preserved; the English publication utility is separate.

Before declaring a fresh run final, resolve every secondary-review disagreement against the source documents. Append decisions to the relevant stage's `review_decisions.jsonl`, preserving primary and secondary labels. Then regenerate the campaign report and validate:

```bash
python poc/campaign_report.py poc/results/NEW_RUN_ID
python poc/validate_campaign.py poc/results/NEW_RUN_ID
```

The orchestrator freezes the current input and executable hashes at initialization and rejects unexpected changes during a campaign. `--resume` is available for an existing incomplete stage; do not silently rerun selected bad answers or combine duplicate answers. The actual October 14 exporter repair is documented in the manifest and event log.

The frozen scripts under `inputs/scripts/` are audit copies, not a standalone installation tree. The top-level `poc/` layout is the executable harness. The question audit and source corpus are needed by the preflight/validator.

## Expected scope and limits

The recorded evaluation uses direct `AgenticSearch.search()` SDK calls in Docker. Sirchmunk invokes the configured LLM API internally. This does not test the Sirchmunk HTTP API or UI.

Parsed-text caches are shared to avoid penalizing the first run for initial extraction. Cluster stores remain isolated. C reuses only earlier clusters from C, not from A or B. It does not repeat exactly identical questions.

Results can vary on a new run. One-pass scores and model-based grading do not guarantee identical reproduction of answers, timings, or labels. Preserve new raw logs and re-adjudicate rather than expecting the published labels to apply automatically.
