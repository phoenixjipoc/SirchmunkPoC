# Handoff: Sirchmunk PoC Evaluation

## 1. Goal

Decide whether **Sirchmunk** (ModelScope's open-source, embedding-free agentic search engine) is viable as the retrieval layer for our internal document Q&A. It would replace or complement the current knowledge base, which parses documents by structure and chunks them.

The PoC must answer four questions with data:

1. **Accuracy at our scale.** One ingest batch is 1,000–2,000+ files. Does answer accuracy hold up?
2. **Low-distinctiveness documents.** Can it tell apart near-duplicate documents, especially the RFPs and DDQs in the shared folder?
3. **Question granularity.** How does it perform across three tiers: detail, medium-range, and broad? Broad questions are a known weakness of our current fine-grained KB, because the retrieval agent struggles when chunks are too small.
4. **Latency and cost.** Is it fast enough? Sampling is expected to be the most time-consuming step.

Background: this came out of a meeting with Phillip. Sirchmunk's three modes are FILENAME_ONLY, FAST and DEEP. DEEP is the full mode and uses Monte Carlo evidence sampling. Phillip stressed that its knowledge clusters "evolve" and are rebuilt, rather than acting as a plain cache.

**Current state:** Sirchmunk is already running locally in Docker Desktop. Nothing else has been built yet: no test corpus, question set, or evaluation scripts.

---

## 2. Decisions made and why

| Decision | Why |
|---|---|
| Use the **already-converted Markdown files** as the corpus | Isolates retrieval quality from parsing quality. This was agreed in the meeting. |
| Use **non-sensitive documents only** | Document content is sent to an external LLM API during search. |
| Corpus in **three nested tiers**: S ≈ 100, M ≈ 500, L ≈ 1,000–2,000 files (S ⊂ M ⊂ L) | Nesting lets the same question set run on every tier, so accuracy and latency degradation can be attributed to scale alone. |
| **Deliberately include near-duplicate docs** (e.g. DDQs for the same product in different years, RFP responses for different clients) | Low distinctiveness is the core risk Phillip raised. A clean corpus would hide it. |
| Question set of **60–80 questions**: ~25 detail, ~20 medium, ~15 broad, ~10 similar-question pairs, ~5 unanswerable | Matches the meeting's three granularity tiers ("several dozen" questions). Pairs test cluster-reuse misjudgment; unanswerable questions test hallucination. |
| Every question records a **gold source file**, not only a gold answer | Lets us score retrieval (Hit@k) separately from generation, which tells us where failures happen. |
| **Always set `mode` explicitly** in every request | The default changed between versions (FAST → DEEP in newer releases). Relying on the default makes results irreproducible. |
| **Clear knowledge clusters before every comparative run** | Before searching files, Sirchmunk checks the query against stored clusters by cosine similarity. If the match is above `cluster_sim_threshold` (default 0.85), it returns the cached cluster and skips retrieval entirely. Leftover clusters from earlier runs would contaminate results. |
| **Prioritised test matrix** instead of the full combination (see §6) | 2 modes × 3 tiers × compile on/off × clusters on/off is too many runs for the value they add. |
| **Run serially first**, add concurrency later | Keeps latency numbers clean. Concurrency is controlled by `SIRCHMUNK_MAX_CONCURRENT_SEARCHES`. |
| Score answers with **LLM-as-judge, plus ~20% human spot-check** | Several dozen questions × many configs is too much to grade by hand. The spot-check calibrates the judge. |
| **Save the full raw JSON response** for every query | Needed to diagnose failures afterwards: was it retrieval, cluster reuse, or synthesis? |

---

## 3. Rejected approaches

| Rejected | Reason |
|---|---|
| Pre-filtering files manually or by rules before search | Not realistic at our file counts. This is the meeting's point 8: our use case differs from Sirchmunk's typical small-corpus use. Simulated *perfect* filtering is kept only as an upper-bound experiment (§7). |
| Re-parsing raw PDFs/DOCX for the PoC | Mixes parsing quality into the result. Markdown is already available. |
| Using sensitive or client documents in the first round | Data leaves the machine via the LLM API. |
| Testing on a single corpus size | Wouldn't answer the scale question, which is the main concern. |
| Accumulating knowledge clusters across comparative runs | Contaminates the results (see §2). Accumulation is tested on purpose, and only in the Evolve experiment. |
| Treating faster repeat runs as proof that "Evolve works" | Speed-up may come from cache hits rather than better knowledge. Accuracy has to be compared too. |
| Full combinatorial test matrix | Too expensive. See the prioritised runs in §6. |

---

## 4. Constraints

- **Environment:** Sirchmunk runs in local Docker Desktop. The API and Web UI share port **8584**. Swagger is at `http://localhost:8584/docs`.
- **LLM:** DEEP and FAST modes need an OpenAI-compatible API key (FILENAME_ONLY doesn't). Record the model name in every result, since it strongly affects accuracy and latency.
- **Version drift:** The project changes fast. Record the exact Sirchmunk version. Check request and response fields against `/docs` for that version before writing parsers.
- **Data:** Non-sensitive Markdown only, at least for this round.
- **Latency expectations from upstream docs:** FAST is roughly 2–5 s with 2 LLM calls; DEEP is roughly 10–30 s. Our numbers at the L tier may be worse. That is what we need to find out.
- **Human effort:** Business colleagues must write and review gold answers. This is the slowest dependency.

---

## 5. Relevant code and config

### 5.1 Docker: mount corpus and work path separately

```bash
# Paths and image name are illustrative. Match them to the existing container setup.
docker run -d --name sirchmunk -p 8584:8584 \
  -v /local/poc_docs:/mnt/docs \
  -v /local/sirchmunk_work:/root/.sirchmunk \
  --env-file .env \
  <sirchmunk-image>

docker logs -f sirchmunk
```

Mount the corpus as `/mnt/docs/S`, `/mnt/docs/M` and `/mnt/docs/L` so a tier is chosen per request through `paths`.

### 5.2 Search API (documented fields)

```python
import requests, time

def search(query, tier="L", mode="DEEP", top_k_files=None):
    body = {"query": query, "paths": [f"/mnt/docs/{tier}"], "mode": mode}
    if top_k_files:
        body["top_k_files"] = top_k_files
    t0 = time.time()
    r = requests.post("http://localhost:8584/api/v1/search", json=body, timeout=300)
    return r.json(), time.time() - t0   # response shape: {"success": bool, "data": ..., "error": ...}
```

Other documented fields are `max_depth` and `top_k_files`. A streaming endpoint is also available at `POST /api/v1/search/stream` (SSE).

Newer versions return the answer, source-linked evidence, retrieval decisions, and token/loop/file-read telemetry, selected via `response_format` (`rich` / `minimal` / `context` / `json`). **Verify the exact field names in `/docs` before writing the parser.**

### 5.3 Knowledge cluster storage (for resetting between runs)

Layout under the work path:

```
~/.sirchmunk/
├── .env
└── .cache/
    ├── knowledge/knowledge_clusters.parquet   # cluster store
    ├── history/chat_history.db
    └── spec/
```

Clusters live in an in-memory DuckDB and are flushed to Parquet periodically and at process exit. The safe reset is therefore: **stop the container → delete `.cache/knowledge/` → start the container.** Deleting the file while the container runs may get overwritten by the next flush.

### 5.4 CLI equivalents (useful for quick manual checks)

```bash
sirchmunk search "question" --mode DEEP --output json --api --api-url http://localhost:8584
sirchmunk compile ...        # optional offline pre-build (Beta); check --help for args
sirchmunk compile --lint     # integrity check
```

### 5.5 Unknowns to verify in code

- Whether `cluster_sim_threshold` can be set through the HTTP API or an environment variable, or only through the Python SDK (`AgenticSearch(..., cluster_sim_threshold=...)`). The threshold-sweep experiment depends on this. If it is SDK-only, run that experiment through the Python SDK inside the container.
- Whether the response flags a cluster-reuse hit. If not, infer it from near-zero file reads or LLM calls in the telemetry.
- The exact `compile` arguments, and whether compile artifacts are picked up automatically for a given path. Upstream says they are detected automatically, with a fallback when absent.

---

## 6. Test plan (in priority order)

1. **Baseline:** S tier × {FAST, DEEP} × no compile × clusters cleared. Confirms the harness and the system work.
2. **Scale:** {M, L} tiers × DEEP × no compile × clusters cleared. **This is the most important run.**
3. **Pre-build:** L tier × DEEP × compile × clusters cleared. Also record how long compile takes.
4. **Similar-question misjudgment:** clear clusters → ask A → ask B (similar wording, different answer) → check whether B returns A's cluster. Repeat at threshold values 0.85, 0.90 and 0.95, if the threshold is configurable.
5. **Evolve:** don't clear clusters. Run the full set 2–3 times in shuffled order and compare both accuracy *and* latency between rounds.

### Metrics

| Metric | Definition |
|---|---|
| Retrieval Hit@k | Gold source file appears in the cited sources |
| Answer accuracy | Judge label: correct / partial / wrong |
| Hallucination rate | Share of unanswerable questions that got a fabricated answer |
| Similar-pair misjudgment | Share of B questions that returned A's answer |
| Latency | P50 / P95, split by question type and mode |
| Cost | Mean tokens per query |

Report a cross-table of **question type × mode × tier**. Look closest at broad questions on the L tier and at errors on the RFP/DDQ near-duplicates.

---

## 7. Optional: routing upper bound (feeds the meeting's next steps)

Run the same questions twice: once over the whole L tier, and once with `paths` restricted by hand to the correct subfolder (e.g. DDQ only). The second run simulates a perfect router. The accuracy gap between the two is the most that routing or document tagging could gain. If the gap is large, it's worth designing routing and query augmentation.

---

## 8. Next step (start here)

**Build the evaluation harness.** Concretely:

1. Call `GET /docs` or the OpenAPI JSON for the running instance. Record the version and the actual request and response schemas. Answer the unknowns in §5.5.
2. Create a `poc/` directory with:
   - `questions_template.csv` with columns `id, question, type (detail|medium|broad|pair_a|pair_b|unanswerable), pair_id, gold_answer, gold_source_file, gold_passage`
   - `run_eval.py` that reads the questions, runs one config (`--tier`, `--mode`, `--reset-clusters`), and writes `results/<run_id>/raw/*.json` and `results/<run_id>/results.csv` (answer, cited sources, latency, tokens, LLM calls, cluster-hit flag)
   - `judge.py` that runs LLM-as-judge on `results.csv` and adds `hit_at_k`, `judge_label` and `judge_reason`
   - `report.py` that aggregates all runs into the type × mode × tier tables
   - `reset_clusters.sh` that stops the container, deletes `.cache/knowledge/`, and starts the container again
3. Smoke-test end to end on the S tier with 5 dummy questions until real questions arrive from business colleagues.

---

## 9. Open questions (not blocking the next step)

- "AOP & ATP" from the meeting's next-steps list is unclear. Confirm with the user what it refers to.
- Success criteria are not agreed yet. Suggested shape: "L tier, DEEP: detail accuracy ≥ X%, P95 latency ≤ Y s". Align with Phillip before the final report.
- Which LLM and model to use for search, and which for judging. Ideally they are different, to avoid self-grading bias.
