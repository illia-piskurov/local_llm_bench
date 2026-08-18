# llm-probe benchmark report

| | |
|---|---|
| **Run** | `2026-08-18T15-10-45-604Z_google-gemma-4-e2b_b5bb3ad1` |
| **Status** | completed |
| **Model** | `google/gemma-4-e2b` |
| **Hardware** | AMD RYZEN 7 250 | 32 GB 5600 | 780m Radeon |
| **Started** | 2026-08-18T15:10:45.604Z |
| **Completed** | 2026-08-18T15:40:58.533Z |
| **Samples (k)** | 1 |
| **Tasks** | 27 |

## Accuracy

| Metric | Value |
|---|---|
| **success@1 (0-shot)** | 17/27 (63%) |

## Accuracy by category

| Category | Pass rate | Tasks |
|---|---|---|
| **product** | 6/14 (43%) | 14 |
| **strings** | 1/1 (100%) | 1 |
| **collections** | 2/2 (100%) | 2 |
| **numbers** | 1/1 (100%) | 1 |
| **structures** | 1/1 (100%) | 1 |
| **algorithms** | 3/3 (100%) | 3 |
| **correctness** | 3/3 (100%) | 3 |
| **evolution** | 0/2 (0%) | 2 |

## Latency & throughput

| | |
|---|---|
| Mean generation | 62600 ms |
| Median generation | 65117 ms |
| Min / Max | 0 ms / 95572 ms |
| Mean tok/s | **29** tok/s |
| Total completion tokens | 48158 (1784 tok/task) |
| **Quality/Speed Score** | **78.7** |

## Failure breakdown

| Failure type | Count |
|---|---|
| failed | 5 |
| runtime_error | 3 |
| provider_error | 1 |
| timeout | 1 |

## Results by task

| Task | Status | Tests | Gen ms | tok/s | Finish |
|---|---|---|---|---|---|
| flat-to-tree | passed | 4/4 | 56906 | 28 | stop |
| paginate-and-sort | passed | 4/4 | 66514 | 27 | stop |
| deep-merge | passed | 4/4 | 84034 | 29 | stop |
| csv-parse | runtime_error | 0/4 | 75494 | 27 | stop |
| render-template | passed | 4/4 | 60901 | 25 | stop |
| shopping-cart | passed | 4/4 | 73872 | 22 | stop |
| query-string-parser | provider_error | 0/0 | 0 | — | — |
| schema-validator | failed | 3/4 | 63942 | 30 | stop |
| state-reducer | runtime_error | 0/4 | 74244 | 30 | stop |
| rbac-checker | failed | 1/3 | 59799 | 30 | stop |
| i18n-pluralize | passed | 3/3 | 49197 | 30 | stop |
| sql-query-builder | runtime_error | 0/3 | 78037 | 29 | stop |
| json-schema-deref-validate | failed | 1/3 | 65348 | 30 | stop |
| cron-next-runs | timeout | 1/3 | 73267 | 30 | stop |
| longest-substring-no-repeat | passed | 5/5 | 69705 | 31 | stop |
| group-anagrams | passed | 5/5 | 53426 | 31 | stop |
| top-k-frequent | passed | 5/5 | 41729 | 29 | stop |
| merge-intervals | passed | 6/6 | 65117 | 29 | stop |
| flatten-tree | passed | 4/4 | 55275 | 29 | stop |
| shortest-path-grid | passed | 4/4 | 51845 | 29 | stop |
| lcs-length | passed | 5/5 | 44523 | 28 | stop |
| topological-sort | passed | 5/5 | 48912 | 25 | stop |
| rotate-square-matrix | passed | 4/4 | 95572 | 28 | stop |
| validate-sudoku-board | passed | 4/4 | 70805 | 28 | stop |
| deep-equal | passed | 8/8 | 53089 | 30 | stop |
| bytecode-vm-evolution | failed | 0/6 | 76895 | 30 | stop |
| event-emitter-evolution | failed | 2/3 | 81744 | 28 | stop |

## Failure details

- `csv-parse`: runtime_error — not a function
- `query-string-parser`: provider_error — Request to http://127.0.0.1:1234/v1 timed out after 120000ms
- `schema-validator`: failed
- `state-reducer`: runtime_error — 'state' is read-only
- `rbac-checker`: failed
- `sql-query-builder`: runtime_error — value is not iterable
- `json-schema-deref-validate`: failed
- `cron-next-runs`: timeout — interrupted
- `bytecode-vm-evolution`: failed
- `event-emitter-evolution`: failed
