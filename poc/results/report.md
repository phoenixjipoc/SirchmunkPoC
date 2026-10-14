# Sirchmunk PoC results

Columns: correct includes correct refusals on unanswerable questions; wrong includes hallucinations. gold@cand/sampled/evidence = the gold file was among the retrieval candidates / among the files sampled for evidence (top_k_files) / in the final evidence. Latency in seconds; tokens = mean total LLM tokens per question.

## 20261007-155154_S_DEEP_baseline
tier S (81 files), mode DEEP, cluster reuse True (threshold 0.85), top_k_files 5, model gpt-5.4, judge gpt-5.4, warmup {'rga_cache': '/poc_cache/rga_S', 'rga_cache_was_empty': False, 'rga_warmup_s': 0.4, 'embedding_load_s': 8.9}

| group | n | correct | partial | wrong | no_answer | gold@cand | gold@sampled | gold@evidence | p50_s | p95_s | tokens |
|---|---|---|---|---|---|---|---|---|---|---|---|
| ALL | 48 | 48% | 10% | 17% | 25% | 80% | 58% | 58% | 35 | 44 | 43,861 |
| detail | 24 | 67% | 8% | 8% | 17% | 96% | 79% | 79% | 34 | 37 | 45,557 |
| pair_a | 7 | 43% | 0% | 0% | 57% | 86% | 43% | 43% | 37 | 41 | 53,809 |
| pair_b | 7 | 0% | 14% | 43% | 43% | 29% | 14% | 14% | 30 | 42 | 31,842 |
| medium | 4 | 25% | 25% | 25% | 25% | 100% | 50% | 50% | 40 | 46 | 54,159 |
| broad | 3 | 0% | 33% | 67% | 0% | 33% | 33% | 33% | 26 | 45 | 26,257 |
| unanswerable | 3 | 100% | 0% | 0% | 0% | - | - | - | 27 | 39 | 38,991 |

- Summary gate blocked 12 answers; 0 of them were correct/partial before the gate.
- rga timeouts: 0; cluster reuse hits: 4
- Pairs: 7; both correct: 0; pair_b reused a cluster: 3

## 20261007-162005_S_DEEP_noreuse
tier S (81 files), mode DEEP, cluster reuse False (threshold 0.85), top_k_files 5, model gpt-5.4, judge gpt-5.4, warmup {'rga_cache': '/poc_cache/rga_S', 'rga_cache_was_empty': False, 'rga_warmup_s': 0.3}

| group | n | correct | partial | wrong | no_answer | gold@cand | gold@sampled | gold@evidence | p50_s | p95_s | tokens |
|---|---|---|---|---|---|---|---|---|---|---|---|
| ALL | 48 | 48% | 8% | 12% | 31% | 91% | 62% | 62% | 35 | 40 | 46,133 |
| detail | 24 | 58% | 8% | 12% | 21% | 96% | 75% | 75% | 34 | 39 | 43,397 |
| pair_a | 7 | 29% | 14% | 0% | 57% | 100% | 43% | 43% | 33 | 40 | 55,561 |
| pair_b | 7 | 29% | 0% | 14% | 57% | 86% | 29% | 29% | 36 | 38 | 56,068 |
| medium | 4 | 50% | 25% | 0% | 25% | 100% | 100% | 100% | 38 | 48 | 45,294 |
| broad | 3 | 0% | 0% | 67% | 33% | 33% | 33% | 33% | 17 | 38 | 25,330 |
| unanswerable | 3 | 100% | 0% | 0% | 0% | - | - | - | 26 | 35 | 44,760 |

- Summary gate blocked 15 answers; 0 of them were correct/partial before the gate.
- rga timeouts: 0; cluster reuse hits: 0
- Pairs: 7; both correct: 1; pair_b reused a cluster: 0

## 20261007-164806_S_DEEP_noreuse_k10
tier S (81 files), mode DEEP, cluster reuse False (threshold 0.85), top_k_files 10, model gpt-5.4, judge gpt-5.4, warmup {'rga_cache': '/poc_cache/rga_S', 'rga_cache_was_empty': False, 'rga_warmup_s': 0.3}

| group | n | correct | partial | wrong | no_answer | gold@cand | gold@sampled | gold@evidence | p50_s | p95_s | tokens |
|---|---|---|---|---|---|---|---|---|---|---|---|
| ALL | 48 | 60% | 12% | 6% | 21% | 98% | 73% | 73% | 39 | 51 | 83,390 |
| detail | 24 | 71% | 12% | 4% | 12% | 100% | 88% | 88% | 37 | 44 | 78,101 |
| pair_a | 7 | 71% | 0% | 0% | 29% | 100% | 71% | 71% | 40 | 56 | 102,689 |
| pair_b | 7 | 29% | 0% | 14% | 57% | 100% | 29% | 29% | 42 | 53 | 102,750 |
| medium | 4 | 50% | 25% | 0% | 25% | 100% | 75% | 75% | 44 | 51 | 79,170 |
| broad | 3 | 0% | 67% | 33% | 0% | 67% | 67% | 67% | 37 | 51 | 63,615 |
| unanswerable | 3 | 100% | 0% | 0% | 0% | - | - | - | 32 | 40 | 60,889 |

- Summary gate blocked 10 answers; 0 of them were correct/partial before the gate.
- rga timeouts: 0; cluster reuse hits: 0
- Pairs: 7; both correct: 1; pair_b reused a cluster: 0
