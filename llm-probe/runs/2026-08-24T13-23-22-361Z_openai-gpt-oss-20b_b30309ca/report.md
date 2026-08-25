# llm-probe benchmark report

| | |
|---|---|
| **Run** | `2026-08-24T13-23-22-361Z_openai-gpt-oss-20b_b30309ca` |
| **Status** | completed |
| **Model** | `openai/gpt-oss-20b` |
| **Hardware** | AMD Ryzen 7 7735HS | 32GB 5600 | 680m Radeon |
| **Started** | 2026-08-24T13:23:22.361Z |
| **Completed** | 2026-08-24T13:47:55.551Z |
| **Samples (k)** | 1 |
| **Tasks** | 27 |

## Accuracy

| Metric | Value |
|---|---|
| **success@1 (0-shot)** | 18/27 (67%) |

## Accuracy by category

| Category | Pass rate | Tasks |
|---|---|---|
| **product** | 9/14 (64%) | 14 |
| **strings** | 1/1 (100%) | 1 |
| **collections** | 2/2 (100%) | 2 |
| **numbers** | 0/1 (0%) | 1 |
| **structures** | 1/1 (100%) | 1 |
| **algorithms** | 2/3 (67%) | 3 |
| **correctness** | 2/3 (67%) | 3 |
| **evolution** | 1/2 (50%) | 2 |

## Latency & throughput

| | |
|---|---|
| Mean generation | 43823 ms |
| Median generation | 36675 ms |
| Min / Max | 0 ms / 154783 ms |
| Mean tok/s | **9** tok/s |
| Total completion tokens | 10659 (395 tok/task) |
| **Quality/Speed Score** | **41.3** |

## Failure breakdown

| Failure type | Count |
|---|---|
| provider_error | 6 |
| failed | 2 |
| timeout | 1 |

## Results by task

| Task | Status | Tests | Gen ms | tok/s | Finish |
|---|---|---|---|---|---|
| flat-to-tree | passed | 4/4 | 41366 | 9 | stop |
| paginate-and-sort | provider_error | 0/0 | 0 | — | — |
| deep-merge | provider_error | 0/0 | 0 | — | — |
| csv-parse | failed | 2/4 | 154783 | 9 | stop |
| render-template | passed | 4/4 | 29386 | 9 | stop |
| shopping-cart | passed | 4/4 | 43194 | 9 | stop |
| query-string-parser | passed | 5/5 | 70295 | 9 | stop |
| schema-validator | passed | 4/4 | 72311 | 9 | stop |
| state-reducer | passed | 4/4 | 59494 | 9 | stop |
| rbac-checker | passed | 3/3 | 40691 | 9 | stop |
| i18n-pluralize | passed | 3/3 | 39263 | 9 | stop |
| sql-query-builder | passed | 3/3 | 109412 | 9 | stop |
| json-schema-deref-validate | failed | 1/3 | 117929 | 9 | stop |
| cron-next-runs | timeout | 1/3 | 112397 | 9 | stop |
| longest-substring-no-repeat | passed | 5/5 | 19179 | 9 | stop |
| group-anagrams | passed | 5/5 | 28300 | 9 | stop |
| top-k-frequent | passed | 5/5 | 31246 | 9 | stop |
| merge-intervals | provider_error | 0/0 | 0 | — | — |
| flatten-tree | passed | 4/4 | 16084 | 8 | stop |
| shortest-path-grid | provider_error | 0/0 | 0 | — | — |
| lcs-length | passed | 5/5 | 28746 | 9 | stop |
| topological-sort | passed | 5/5 | 26915 | 9 | stop |
| rotate-square-matrix | provider_error | 0/0 | 0 | — | — |
| validate-sudoku-board | passed | 4/4 | 39178 | 9 | stop |
| deep-equal | passed | 8/8 | 36675 | 9 | stop |
| bytecode-vm-evolution | provider_error | 0/0 | 0 | — | — |
| event-emitter-evolution | passed | 3/3 | 66388 | 9 | stop |

## Failure details

- `paginate-and-sort`: provider_error — Provider returned HTTP 400
- `deep-merge`: provider_error — Provider returned HTTP 400
- `csv-parse`: failed
- `json-schema-deref-validate`: failed
- `cron-next-runs`: timeout — interrupted
- `merge-intervals`: provider_error — Provider returned HTTP 400
- `shortest-path-grid`: provider_error — Provider returned HTTP 400
- `rotate-square-matrix`: provider_error — Provider returned HTTP 400
- `bytecode-vm-evolution`: provider_error — Provider returned HTTP 400
