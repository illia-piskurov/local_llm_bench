# 🏆 llm-probe Benchmark Leaderboard

> Updated: 2026-08-18 20:30:31 UTC | Total models/configurations benchmarked: **7**

---

## 📊 Master Table (All Metrics)

| # | Model | Hardware | Accuracy | Speed | Mean Latency | Total Tokens | Q/S Score |
|---|---|---|---|---|---|---|---|
| **1** | `google/gemma-4-e2b` | AMD RYZEN 7 250 | 32 GB 5600 | 780m Radeon | **17/27** (63%) | **28.5** tok/s | 62600 ms | 48158 | **77.9** |
| **2** | `google/gemma-4-e4b` | AMD RYZEN 7 250 | 32 GB 5600 | 780m Radeon | **19/27** (70.4%) | **17.7** tok/s | 112637 ms | 53702 | **65.4** |
| **3** | `ibm/granite-4-h-tiny` | AMD RYZEN 7 250 | 32 GB 5600 | 780m Radeon | **11/27** (40.7%) | **28.2** tok/s | 11786 ms | 8992 | **50** |
| **4** | `mistralai/ministral-3-3b` | AMD RYZEN 7 250 | 32 GB 5600 | 780m Radeon | **10/27** (37%) | **18.3** tok/s | 18756 ms | 9087 | **35.1** |
| **5** | `liquid/lfm2.5-1.2b` | AMD RYZEN 7 250 | 32 GB 5600 | 780m Radeon | **3/27** (11.1%) | **48** tok/s | 6177 ms | 7996 | **18.8** |
| **6** | `bonsai-8b` | AMD RYZEN 7 250 | 32 GB 5600 | 780m Radeon | **2/27** (7.4%) | **23.5** tok/s | 16254 ms | 10032 | **8.2** |
| **7** | `google/gemma-4-12b-qat` | AMD RYZEN 7 250 | 32 GB 5600 | 780m Radeon | **0/27** (0%) | **0** tok/s | 0 ms | 0 | **0** |

## 🎯 1. Quality Ranking (Accuracy / Pass Rate)
> Ranked strictly by success rate across benchmark tasks (higher is better).

| Rank | Model | Hardware | Pass Rate | Tasks Passed | Q/S Score |
|---|---|---|---|---|---|
| 🥇 1 | `google/gemma-4-e4b` | AMD RYZEN 7 250 | 32 GB 5600 | 780m Radeon | **70.4%** | 19/27 | 65.4 |
| 🥈 2 | `google/gemma-4-e2b` | AMD RYZEN 7 250 | 32 GB 5600 | 780m Radeon | **63%** | 17/27 | 77.9 |
| 🥉 3 | `ibm/granite-4-h-tiny` | AMD RYZEN 7 250 | 32 GB 5600 | 780m Radeon | **40.7%** | 11/27 | 50 |
| 4 | `mistralai/ministral-3-3b` | AMD RYZEN 7 250 | 32 GB 5600 | 780m Radeon | **37%** | 10/27 | 35.1 |
| 5 | `liquid/lfm2.5-1.2b` | AMD RYZEN 7 250 | 32 GB 5600 | 780m Radeon | **11.1%** | 3/27 | 18.8 |
| 6 | `bonsai-8b` | AMD RYZEN 7 250 | 32 GB 5600 | 780m Radeon | **7.4%** | 2/27 | 8.2 |
| 7 | `google/gemma-4-12b-qat` | AMD RYZEN 7 250 | 32 GB 5600 | 780m Radeon | **0%** | 0/27 | 0 |

## ⚡ 2. Speed Ranking (Generation Throughput)
> Ranked strictly by generation throughput in tokens per second (higher is faster).

| Rank | Model | Hardware | Throughput | Median Latency | Mean Latency |
|---|---|---|---|---|---|
| 🥇 1 | `liquid/lfm2.5-1.2b` | AMD RYZEN 7 250 | 32 GB 5600 | 780m Radeon | **48 tok/s** | 4817 ms | 6177 ms |
| 🥈 2 | `google/gemma-4-e2b` | AMD RYZEN 7 250 | 32 GB 5600 | 780m Radeon | **28.5 tok/s** | 65117 ms | 62600 ms |
| 🥉 3 | `ibm/granite-4-h-tiny` | AMD RYZEN 7 250 | 32 GB 5600 | 780m Radeon | **28.2 tok/s** | 7542 ms | 11786 ms |
| 4 | `bonsai-8b` | AMD RYZEN 7 250 | 32 GB 5600 | 780m Radeon | **23.5 tok/s** | 14535 ms | 16254 ms |
| 5 | `mistralai/ministral-3-3b` | AMD RYZEN 7 250 | 32 GB 5600 | 780m Radeon | **18.3 tok/s** | 14548 ms | 18756 ms |
| 6 | `google/gemma-4-e4b` | AMD RYZEN 7 250 | 32 GB 5600 | 780m Radeon | **17.7 tok/s** | 114311 ms | 112637 ms |
| 7 | `google/gemma-4-12b-qat` | AMD RYZEN 7 250 | 32 GB 5600 | 780m Radeon | **0 tok/s** | 0 ms | 0 ms |

## 💡 3. Token Efficiency Ranking (Conciseness)
> Ranked by fewest tokens spent per task (more concise & focused solutions).

| Rank | Model | Hardware | Tokens / Task | Total Tokens | Accuracy |
|---|---|---|---|---|---|
| 🥇 1 | `google/gemma-4-12b-qat` | AMD RYZEN 7 250 | 32 GB 5600 | 780m Radeon | **0** tok/task | 0 | 0% |
| 🥈 2 | `liquid/lfm2.5-1.2b` | AMD RYZEN 7 250 | 32 GB 5600 | 780m Radeon | **296** tok/task | 7996 | 11.1% |
| 🥉 3 | `ibm/granite-4-h-tiny` | AMD RYZEN 7 250 | 32 GB 5600 | 780m Radeon | **333** tok/task | 8992 | 40.7% |
| 4 | `mistralai/ministral-3-3b` | AMD RYZEN 7 250 | 32 GB 5600 | 780m Radeon | **337** tok/task | 9087 | 37% |
| 5 | `bonsai-8b` | AMD RYZEN 7 250 | 32 GB 5600 | 780m Radeon | **372** tok/task | 10032 | 7.4% |
| 6 | `google/gemma-4-e2b` | AMD RYZEN 7 250 | 32 GB 5600 | 780m Radeon | **1784** tok/task | 48158 | 63% |
| 7 | `google/gemma-4-e4b` | AMD RYZEN 7 250 | 32 GB 5600 | 780m Radeon | **1989** tok/task | 53702 | 70.4% |

## ⚖️ 4. Balanced Quality/Speed Index (Q/S Score)
> Composite index: $\text{Score} = \text{Accuracy(\%)} \times (\text{tok/s} / 20)^{0.6}$. Rewards high quality with strong speed weighting.

| Rank | Model | Hardware | Q/S Score | Accuracy | Speed |
|---|---|---|---|---|---|
| 🥇 1 | `google/gemma-4-e2b` | AMD RYZEN 7 250 | 32 GB 5600 | 780m Radeon | **77.9** | 63% | 28.5 tok/s |
| 🥈 2 | `google/gemma-4-e4b` | AMD RYZEN 7 250 | 32 GB 5600 | 780m Radeon | **65.4** | 70.4% | 17.7 tok/s |
| 🥉 3 | `ibm/granite-4-h-tiny` | AMD RYZEN 7 250 | 32 GB 5600 | 780m Radeon | **50** | 40.7% | 28.2 tok/s |
| 4 | `mistralai/ministral-3-3b` | AMD RYZEN 7 250 | 32 GB 5600 | 780m Radeon | **35.1** | 37% | 18.3 tok/s |
| 5 | `liquid/lfm2.5-1.2b` | AMD RYZEN 7 250 | 32 GB 5600 | 780m Radeon | **18.8** | 11.1% | 48 tok/s |
| 6 | `bonsai-8b` | AMD RYZEN 7 250 | 32 GB 5600 | 780m Radeon | **8.2** | 7.4% | 23.5 tok/s |
| 7 | `google/gemma-4-12b-qat` | AMD RYZEN 7 250 | 32 GB 5600 | 780m Radeon | **0** | 0% | 0 tok/s |
