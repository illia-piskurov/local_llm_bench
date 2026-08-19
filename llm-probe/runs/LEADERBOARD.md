# 🏆 llm-probe Benchmark Leaderboard

> Updated: 2026-08-19 08:42:42 UTC | Total models/configurations benchmarked: **12**

---

## 📊 Master Table (All Metrics)

| # | Model | Hardware | Accuracy | Speed | Mean Latency | Total Tokens | Q/S Score |
|---|---|---|---|---|---|---|---|
| **1** | `google/gemma-4-e2b` | AMD RYZEN 7 250 | 32 GB 5600 | 780m Radeon | **17/27** (63%) | **28.5** tok/s | 62600 ms | 48158 | **77.9** |
| **2** | `google/gemma-4-e4b` | AMD RYZEN 7 250 | 32 GB 5600 | 780m Radeon | **19/27** (70.4%) | **17.7** tok/s | 112637 ms | 53702 | **65.4** |
| **3** | `mistralai/ministral-3-3b` | Unspecified Hardware | **11/17** (64.7%) | **18.6** tok/s | 7613 ms | 2416 | **61.9** |
| **4** | `qwen/qwen3-4b-2507` | AMD Ryzen 7 7735HS | 32GB 5600 | 680m Radeon | **16/27** (59.3%) | **18.6** tok/s | 28856 ms | 14532 | **56.8** |
| **5** | `ibm/granite-4-h-tiny` | AMD RYZEN 7 250 | 32 GB 5600 | 780m Radeon | **11/27** (40.7%) | **28.2** tok/s | 11786 ms | 8992 | **50** |
| **6** | `mistralai/ministral-3-3b` | AMD RYZEN 7 250 | 32 GB 5600 | 780m Radeon | **10/27** (37%) | **18.3** tok/s | 18756 ms | 9087 | **35.1** |
| **7** | `liquid/lfm2.5-1.2b` | AMD RYZEN 7 250 | 32 GB 5600 | 780m Radeon | **3/27** (11.1%) | **48** tok/s | 6177 ms | 7996 | **18.8** |
| **8** | `bonsai-8b` | AMD RYZEN 7 250 | 32 GB 5600 | 780m Radeon | **2/27** (7.4%) | **23.5** tok/s | 16254 ms | 10032 | **8.2** |
| **9** | `google/gemma-3-1b` | AMD Ryzen 7 7735HS | 32GB 5600 | 680m Radeon | **1/27** (3.7%) | **42.3** tok/s | 5054 ms | 5965 | **5.8** |
| **10** | `microsoft/phi-4-mini-reasoning` | AMD Ryzen 7 7735HS | 32GB 5600 | 680m Radeon | **0/27** (0%) | **0** tok/s | 0 ms | 0 | **0** |
| **11** | `nvidia/nemotron-3-nano-4b` | AMD Ryzen 7 7735HS | 32GB 5600 | 680m Radeon | **0/27** (0%) | **10.8** tok/s | 199568 ms | 8455 | **0** |
| **12** | `google/gemma-4-12b-qat` | AMD RYZEN 7 250 | 32 GB 5600 | 780m Radeon | **0/27** (0%) | **0** tok/s | 0 ms | 0 | **0** |

## 🎯 1. Quality Ranking (Accuracy / Pass Rate)
> Ranked strictly by success rate across benchmark tasks (higher is better).

| Rank | Model | Hardware | Pass Rate | Tasks Passed | Q/S Score |
|---|---|---|---|---|---|
| 🥇 1 | `google/gemma-4-e4b` | AMD RYZEN 7 250 | 32 GB 5600 | 780m Radeon | **70.4%** | 19/27 | 65.4 |
| 🥈 2 | `mistralai/ministral-3-3b` | Unspecified Hardware | **64.7%** | 11/17 | 61.9 |
| 🥉 3 | `google/gemma-4-e2b` | AMD RYZEN 7 250 | 32 GB 5600 | 780m Radeon | **63%** | 17/27 | 77.9 |
| 4 | `qwen/qwen3-4b-2507` | AMD Ryzen 7 7735HS | 32GB 5600 | 680m Radeon | **59.3%** | 16/27 | 56.8 |
| 5 | `ibm/granite-4-h-tiny` | AMD RYZEN 7 250 | 32 GB 5600 | 780m Radeon | **40.7%** | 11/27 | 50 |
| 6 | `mistralai/ministral-3-3b` | AMD RYZEN 7 250 | 32 GB 5600 | 780m Radeon | **37%** | 10/27 | 35.1 |
| 7 | `liquid/lfm2.5-1.2b` | AMD RYZEN 7 250 | 32 GB 5600 | 780m Radeon | **11.1%** | 3/27 | 18.8 |
| 8 | `bonsai-8b` | AMD RYZEN 7 250 | 32 GB 5600 | 780m Radeon | **7.4%** | 2/27 | 8.2 |
| 9 | `google/gemma-3-1b` | AMD Ryzen 7 7735HS | 32GB 5600 | 680m Radeon | **3.7%** | 1/27 | 5.8 |
| 10 | `microsoft/phi-4-mini-reasoning` | AMD Ryzen 7 7735HS | 32GB 5600 | 680m Radeon | **0%** | 0/27 | 0 |
| 11 | `nvidia/nemotron-3-nano-4b` | AMD Ryzen 7 7735HS | 32GB 5600 | 680m Radeon | **0%** | 0/27 | 0 |
| 12 | `google/gemma-4-12b-qat` | AMD RYZEN 7 250 | 32 GB 5600 | 780m Radeon | **0%** | 0/27 | 0 |

## ⚡ 2. Speed Ranking (Generation Throughput)
> Ranked strictly by generation throughput in tokens per second (higher is faster).

| Rank | Model | Hardware | Throughput | Median Latency | Mean Latency |
|---|---|---|---|---|---|
| 🥇 1 | `liquid/lfm2.5-1.2b` | AMD RYZEN 7 250 | 32 GB 5600 | 780m Radeon | **48 tok/s** | 4817 ms | 6177 ms |
| 🥈 2 | `google/gemma-3-1b` | AMD Ryzen 7 7735HS | 32GB 5600 | 680m Radeon | **42.3 tok/s** | 4393 ms | 5054 ms |
| 🥉 3 | `google/gemma-4-e2b` | AMD RYZEN 7 250 | 32 GB 5600 | 780m Radeon | **28.5 tok/s** | 65117 ms | 62600 ms |
| 4 | `ibm/granite-4-h-tiny` | AMD RYZEN 7 250 | 32 GB 5600 | 780m Radeon | **28.2 tok/s** | 7542 ms | 11786 ms |
| 5 | `bonsai-8b` | AMD RYZEN 7 250 | 32 GB 5600 | 780m Radeon | **23.5 tok/s** | 14535 ms | 16254 ms |
| 6 | `mistralai/ministral-3-3b` | Unspecified Hardware | **18.6 tok/s** | 6343 ms | 7613 ms |
| 7 | `qwen/qwen3-4b-2507` | AMD Ryzen 7 7735HS | 32GB 5600 | 680m Radeon | **18.6 tok/s** | 21943 ms | 28856 ms |
| 8 | `mistralai/ministral-3-3b` | AMD RYZEN 7 250 | 32 GB 5600 | 780m Radeon | **18.3 tok/s** | 14548 ms | 18756 ms |
| 9 | `google/gemma-4-e4b` | AMD RYZEN 7 250 | 32 GB 5600 | 780m Radeon | **17.7 tok/s** | 114311 ms | 112637 ms |
| 10 | `nvidia/nemotron-3-nano-4b` | AMD Ryzen 7 7735HS | 32GB 5600 | 680m Radeon | **10.8 tok/s** | 156526 ms | 199568 ms |
| 11 | `microsoft/phi-4-mini-reasoning` | AMD Ryzen 7 7735HS | 32GB 5600 | 680m Radeon | **0 tok/s** | 0 ms | 0 ms |
| 12 | `google/gemma-4-12b-qat` | AMD RYZEN 7 250 | 32 GB 5600 | 780m Radeon | **0 tok/s** | 0 ms | 0 ms |

## 💡 3. Token Efficiency Ranking (Conciseness)
> Ranked by fewest tokens spent per task (more concise & focused solutions).

| Rank | Model | Hardware | Tokens / Task | Total Tokens | Accuracy |
|---|---|---|---|---|---|
| 🥇 1 | `microsoft/phi-4-mini-reasoning` | AMD Ryzen 7 7735HS | 32GB 5600 | 680m Radeon | **0** tok/task | 0 | 0% |
| 🥈 2 | `google/gemma-4-12b-qat` | AMD RYZEN 7 250 | 32 GB 5600 | 780m Radeon | **0** tok/task | 0 | 0% |
| 🥉 3 | `mistralai/ministral-3-3b` | Unspecified Hardware | **142** tok/task | 2416 | 64.7% |
| 4 | `google/gemma-3-1b` | AMD Ryzen 7 7735HS | 32GB 5600 | 680m Radeon | **221** tok/task | 5965 | 3.7% |
| 5 | `liquid/lfm2.5-1.2b` | AMD RYZEN 7 250 | 32 GB 5600 | 780m Radeon | **296** tok/task | 7996 | 11.1% |
| 6 | `nvidia/nemotron-3-nano-4b` | AMD Ryzen 7 7735HS | 32GB 5600 | 680m Radeon | **313** tok/task | 8455 | 0% |
| 7 | `ibm/granite-4-h-tiny` | AMD RYZEN 7 250 | 32 GB 5600 | 780m Radeon | **333** tok/task | 8992 | 40.7% |
| 8 | `mistralai/ministral-3-3b` | AMD RYZEN 7 250 | 32 GB 5600 | 780m Radeon | **337** tok/task | 9087 | 37% |
| 9 | `bonsai-8b` | AMD RYZEN 7 250 | 32 GB 5600 | 780m Radeon | **372** tok/task | 10032 | 7.4% |
| 10 | `qwen/qwen3-4b-2507` | AMD Ryzen 7 7735HS | 32GB 5600 | 680m Radeon | **538** tok/task | 14532 | 59.3% |
| 11 | `google/gemma-4-e2b` | AMD RYZEN 7 250 | 32 GB 5600 | 780m Radeon | **1784** tok/task | 48158 | 63% |
| 12 | `google/gemma-4-e4b` | AMD RYZEN 7 250 | 32 GB 5600 | 780m Radeon | **1989** tok/task | 53702 | 70.4% |

## ⚖️ 4. Balanced Quality/Speed Index (Q/S Score)
> Composite index: $\text{Score} = \text{Accuracy(\%)} \times (\text{tok/s} / 20)^{0.6}$. Rewards high quality with strong speed weighting.

| Rank | Model | Hardware | Q/S Score | Accuracy | Speed |
|---|---|---|---|---|---|
| 🥇 1 | `google/gemma-4-e2b` | AMD RYZEN 7 250 | 32 GB 5600 | 780m Radeon | **77.9** | 63% | 28.5 tok/s |
| 🥈 2 | `google/gemma-4-e4b` | AMD RYZEN 7 250 | 32 GB 5600 | 780m Radeon | **65.4** | 70.4% | 17.7 tok/s |
| 🥉 3 | `mistralai/ministral-3-3b` | Unspecified Hardware | **61.9** | 64.7% | 18.6 tok/s |
| 4 | `qwen/qwen3-4b-2507` | AMD Ryzen 7 7735HS | 32GB 5600 | 680m Radeon | **56.8** | 59.3% | 18.6 tok/s |
| 5 | `ibm/granite-4-h-tiny` | AMD RYZEN 7 250 | 32 GB 5600 | 780m Radeon | **50** | 40.7% | 28.2 tok/s |
| 6 | `mistralai/ministral-3-3b` | AMD RYZEN 7 250 | 32 GB 5600 | 780m Radeon | **35.1** | 37% | 18.3 tok/s |
| 7 | `liquid/lfm2.5-1.2b` | AMD RYZEN 7 250 | 32 GB 5600 | 780m Radeon | **18.8** | 11.1% | 48 tok/s |
| 8 | `bonsai-8b` | AMD RYZEN 7 250 | 32 GB 5600 | 780m Radeon | **8.2** | 7.4% | 23.5 tok/s |
| 9 | `google/gemma-3-1b` | AMD Ryzen 7 7735HS | 32GB 5600 | 680m Radeon | **5.8** | 3.7% | 42.3 tok/s |
| 10 | `microsoft/phi-4-mini-reasoning` | AMD Ryzen 7 7735HS | 32GB 5600 | 680m Radeon | **0** | 0% | 0 tok/s |
| 11 | `nvidia/nemotron-3-nano-4b` | AMD Ryzen 7 7735HS | 32GB 5600 | 680m Radeon | **0** | 0% | 10.8 tok/s |
| 12 | `google/gemma-4-12b-qat` | AMD RYZEN 7 250 | 32 GB 5600 | 780m Radeon | **0** | 0% | 0 tok/s |
