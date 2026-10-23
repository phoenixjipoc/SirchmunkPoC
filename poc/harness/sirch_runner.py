"""Runs inside the sirchmunk container. Do not run on the host.

Builds AgenticSearch with the same constructor arguments the HTTP API uses
(sirchmunk/api/search.py::_get_search_instance) and calls search() with the
API's default kwargs. Questions are run serially.

Three methods are wrapped for observation only (behaviour is unchanged), to
record what the HTTP response drops:
  - knowledge_base.build   -> candidate files and the evidence files actually used
  - _summarise_cluster     -> the summary gate verdict and the pre-gate answer text
  - _try_reuse_cluster     -> whether a stored knowledge cluster was reused

Usage (inside container):
  python sirch_runner.py --questions q.jsonl --out-dir /poc_runs/<run_id> \
      --paths /mnt/docs/S --mode DEEP [--work-path /poc_runs/<run_id>/work] \
      [--rga-cache /poc_cache/rga_S]
"""
import argparse
import asyncio
import json
import os
import time
from pathlib import Path

from sirchmunk.llm.openai_chat import OpenAIChat
from sirchmunk.search import AgenticSearch


async def link_and_warm_rga_cache(work_path, cache, paths):
    """Point <work_path>/.cache/rga at a shared cache and pre-extract every document.

    Uses the same --rga-cache-max-blob-len and --rga-cache-path flags that
    sirchmunk's GrepRetriever passes, so its later searches hit this cache.
    Returns timing info. A cold warmup is roughly the cost of first queries
    after a new ingest batch.
    """
    cache.mkdir(parents=True, exist_ok=True)
    link = work_path / ".cache" / "rga"
    link.parent.mkdir(parents=True, exist_ok=True)
    if not link.exists():
        link.symlink_to(cache, target_is_directory=True)
    was_empty = not any(cache.iterdir())
    t0 = time.time()
    proc = await asyncio.create_subprocess_exec(
        "rga", "--no-config", "-l", "--rga-cache-max-blob-len=10000000",
        f"--rga-cache-path={cache.resolve()}", "zq9xwarmupzq9x", *paths,
        stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL)
    await proc.wait()
    secs = round(time.time() - t0, 1)
    print(f"[warmup] rga cache {'cold' if was_empty else 'warm'} pass: {secs}s", flush=True)
    return {"rga_cache": str(cache), "rga_cache_was_empty": was_empty, "rga_warmup_s": secs}


def _cluster_files(cluster, found_only=False):
    if not cluster or not cluster.evidences:
        return []
    return [str(e.file_or_url) for e in (cluster.evidences or [])
            if not found_only or getattr(e, 'is_found', False)]


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--questions", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--paths", nargs="+", required=True)
    ap.add_argument("--mode", default="DEEP", choices=["DEEP", "FAST"])
    ap.add_argument("--work-path", default=None,
                    help="Sirchmunk work path. A fresh dir isolates the knowledge clusters.")
    ap.add_argument("--top-k-files", type=int, default=None)
    ap.add_argument("--question-timeout", type=int, default=600)
    ap.add_argument("--rga-cache", default=None,
                    help="Shared rga text-extraction cache dir. Linked into the work path so "
                         "knowledge clusters start empty while extracted document text stays warm.")
    args = ap.parse_args()

    out_dir = Path(args.out_dir)
    (out_dir / "raw").mkdir(parents=True, exist_ok=True)
    work_path = args.work_path or str(out_dir / "work")

    warmup = {}
    if args.rga_cache:
        warmup.update(await link_and_warm_rga_cache(Path(work_path), Path(args.rga_cache), args.paths))

    model = os.environ["LLM_MODEL_NAME"]
    llm = OpenAIChat(base_url=os.getenv("LLM_BASE_URL", "https://api.openai.com/v1"),
                     api_key=os.getenv("LLM_API_KEY", ""), model=model)

    # Count each actual API wrapper call once, including calls made by child
    # samplers. The library's aggregate usage lists may omit child components.
    call_records = []
    original_achat = llm.achat

    async def tracked_achat(*a, **kw):
        started = time.time()
        try:
            response = await original_achat(*a, **kw)
        except Exception as exc:
            call_records.append({'elapsed_s': round(time.time()-started, 3),
                                 'error': f'{type(exc).__name__}: {exc}', 'usage': {}})
            raise
        usage = getattr(response, 'usage', None) or {}
        if hasattr(usage, 'model_dump'):
            usage = usage.model_dump()
        call_records.append({'elapsed_s': round(time.time()-started, 3),
                             'error': None, 'usage': usage})
        return response

    llm.achat = tracked_achat

    logs = []

    async def log_cb(level, message, *rest):
        logs.append({"t": round(time.time(), 3), "level": level, "msg": message})

    searcher = AgenticSearch(
        llm=llm,
        work_path=work_path,
        verbose=False,
        log_callback=log_cb,
        reuse_knowledge=os.getenv("SIRCHMUNK_ENABLE_CLUSTER_REUSE", "true").lower() == "true",
        cluster_sim_threshold=float(os.getenv("CLUSTER_SIM_THRESHOLD", "0.85")),
        cluster_sim_top_k=int(os.getenv("CLUSTER_SIM_TOP_K", "3")),
    )

    # Load the embedding model up front. Otherwise the first queries skip cluster
    # reuse and compete with the model load for CPU.
    if searcher.embedding_client is not None:
        t0 = time.time()
        searcher.embedding_client.start_loading()
        await searcher.embedding_client._ensure_model_async(timeout=300)
        warmup["embedding_load_s"] = round(time.time() - t0, 1)
        print(f"[warmup] embedding model ready: {warmup['embedding_load_s']}s", flush=True)
    (out_dir / "warmup.json").write_text(json.dumps(warmup, indent=1), encoding="utf-8")

    trace = {}

    kb = searcher.knowledge_base
    orig_build = kb.build

    async def build(*a, **kw):
        infos = kw.get("retrieved_infos") or (a[1] if len(a) > 1 else [])
        k = kw.get("top_k_files") or 3
        trace.setdefault("candidate_files", []).extend(str(i["path"]) for i in infos)
        trace.setdefault("sampled_files", []).extend(str(i["path"]) for i in infos[:k])
        cluster = await orig_build(*a, **kw)
        trace.setdefault("evidence_files", []).extend(_cluster_files(cluster))
        trace.setdefault("evidence_found_files", []).extend(_cluster_files(cluster, found_only=True))
        return cluster

    kb.build = build

    orig_sum = searcher._summarise_cluster

    async def summarise(query, cluster):
        summary, should_save, should_answer = await orig_sum(query, cluster)
        trace.setdefault("gate", []).append({"should_answer": should_answer,
                                             "should_save": should_save,
                                             "summary": summary})
        return summary, should_save, should_answer

    searcher._summarise_cluster = summarise

    orig_reuse = searcher._try_reuse_cluster

    async def reuse(*a, **kw):
        c = await orig_reuse(*a, **kw)
        trace["reused_cluster"] = getattr(c, "name", None) if c else None
        trace["reused_cluster_id"] = getattr(c, 'id', None) if c else None
        trace["reused_cluster_queries"] = list(getattr(c, 'queries', None) or [])
        return c

    searcher._try_reuse_cluster = reuse

    questions = [json.loads(line) for line in open(args.questions, encoding="utf-8") if line.strip()]
    results_path = out_dir / "results.jsonl"
    done = set()
    if results_path.exists():
        done = {json.loads(line)["id"] for line in open(results_path, encoding="utf-8")}

    consecutive_errors = 0
    for i, q in enumerate(questions, 1):
        if q["id"] in done:
            continue
        logs.clear()
        trace.clear()
        call_records.clear()
        usage_start = len(searcher.llm_usages)
        kwargs = {"query": q["question"], "paths": args.paths, "mode": args.mode,
                  "enable_dir_scan": True, "return_context": True, "llm_fallback": False}
        if args.top_k_files:
            kwargs["top_k_files"] = args.top_k_files

        t0 = time.time()
        error = None
        ctx = None
        try:
            ctx = await asyncio.wait_for(searcher.search(**kwargs), timeout=args.question_timeout)
        except Exception as e:
            error = f"{type(e).__name__}: {e}"
        latency = time.time() - t0

        library_usages = [u for u in searcher.llm_usages[usage_start:] if isinstance(u, dict)]
        usages = [r['usage'] for r in call_records if isinstance(r.get('usage'), dict)]
        ctx_dict = None
        if ctx is not None and hasattr(ctx, "to_dict"):
            try:
                ctx_dict = ctx.to_dict()
            except Exception as e:
                # sirchmunk 0.0.7 bug: SearchContext.to_dict() fails when a reused
                # cluster has evidences=None. The HTTP API would return 500 here.
                ctx_dict = {"answer": getattr(ctx, "answer", None),
                            "to_dict_error": f"{type(e).__name__}: {e}"}
        answer = ctx_dict.get("answer") if ctx_dict else None
        if ctx is None and not error:
            error = 'EmptySearchContext: search returned no context'
        failures = [r['error'] for r in call_records if r.get('error')]
        if failures and not any(r.get('usage') for r in call_records):
            error = error or 'LLMCallFailure: ' + failures[-1]
        gate = trace.get("gate", [])
        rec = {
            "id": q["id"],
            "question": q["question"],
            "mode": args.mode,
            "paths": args.paths,
            "model": model,
            "answer": answer,
            "no_result": (answer or "").strip().lower() == "no results found.",
            "gate_should_answer": gate[-1]["should_answer"] if gate else None,
            "pre_gate_answer": gate[-1]["summary"] if gate else None,
            "candidate_files": trace.get("candidate_files", []),
            "sampled_files": trace.get("sampled_files", []),
            "evidence_files": trace.get("evidence_files", []),
            "evidence_found_files": trace.get("evidence_found_files", []),
            "cited_files": _cluster_files(ctx.cluster) if ctx is not None and getattr(ctx, "cluster", None) else [],
            "cited_found_files": _cluster_files(ctx.cluster, found_only=True) if ctx is not None and getattr(ctx, "cluster", None) else [],
            "reused_cluster": trace.get("reused_cluster"),
            "reused_cluster_id": trace.get("reused_cluster_id"),
            "reused_cluster_queries": trace.get("reused_cluster_queries", []),
            "cluster_id": getattr(getattr(ctx, 'cluster', None), 'id', None),
            "latency_s": round(latency, 2),
            "llm_calls": len(call_records),
            "llm_failed_calls": len(failures),
            "prompt_tokens": sum(u.get("prompt_tokens", 0) or 0 for u in usages),
            "completion_tokens": sum(u.get("completion_tokens", 0) or 0 for u in usages),
            "total_tokens": sum(u.get("total_tokens", 0) or 0 for u in usages),
            "error": error,
            "serialization_error": ctx_dict.get('to_dict_error') if ctx_dict else None,
            "warnings": [l["msg"] for l in logs if l["level"] == "warning"],
        }
        raw = {"record": rec, "context": ctx_dict, "logs": list(logs),
               "llm_call_records": list(call_records), "library_usage_records": library_usages,
               "trace": dict(trace)}
        (out_dir / "raw" / f"{q['id']}.json").write_text(
            json.dumps(raw, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
        with open(results_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False, default=str) + "\n")
        status = "ERROR" if error else ("NO_RESULT" if rec["no_result"] else "answered")
        print(f"[{i}/{len(questions)}] {q['id']} {status} {latency:.1f}s "
              f"tokens={rec['total_tokens']} evidence={len(set(rec['evidence_files']))}", flush=True)
        consecutive_errors = consecutive_errors + 1 if error else 0
        fatal_api = any(term in str(failures).lower() for term in
                        ('insufficient_quota', 'invalid_api_key', 'billing_hard_limit', 'authenticationerror'))
        if fatal_api or consecutive_errors >= 3:
            searcher.knowledge_storage.force_sync()
            raise RuntimeError('Stopped after fatal API failure or three consecutive search errors; partial results preserved.')

    searcher.knowledge_storage.force_sync()


if __name__ == "__main__":
    asyncio.run(main())
