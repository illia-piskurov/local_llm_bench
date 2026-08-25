# llm-probe benchmark report

| | |
|---|---|
| **Run** | `2026-08-19T08-17-16-113Z_qwen-qwen3-4b-2507_865abbaf` |
| **Status** | completed |
| **Model** | `qwen/qwen3-4b-2507` |
| **Hardware** | AMD Ryzen 7 7735HS | 32GB 5600 | 680m Radeon |
| **Started** | 2026-08-19T08:17:16.113Z |
| **Completed** | 2026-08-19T08:30:18.215Z |
| **Samples (k)** | 1 |
| **Tasks** | 27 |

## Accuracy

| Metric | Value |
|---|---|
| **success@1 (0-shot)** | 16/27 (59%) |

## Accuracy by category

| Category | Pass rate | Tasks |
|---|---|---|
| **product** | 7/14 (50%) | 14 |
| **strings** | 0/1 (0%) | 1 |
| **collections** | 2/2 (100%) | 2 |
| **numbers** | 1/1 (100%) | 1 |
| **structures** | 1/1 (100%) | 1 |
| **algorithms** | 3/3 (100%) | 3 |
| **correctness** | 2/3 (67%) | 3 |
| **evolution** | 0/2 (0%) | 2 |

## Latency & throughput

| | |
|---|---|
| Mean generation | 28856 ms |
| Median generation | 21943 ms |
| Min / Max | 6123 ms / 119069 ms |
| Mean tok/s | **19** tok/s |
| Total completion tokens | 14532 (538 tok/task) |
| **Quality/Speed Score** | **57.5** |

## Failure breakdown

| Failure type | Count |
|---|---|
| failed | 6 |
| runtime_error | 4 |
| compile_error | 1 |

## Results by task

| Task | Status | Tests | Gen ms | tok/s | Finish |
|---|---|---|---|---|---|
| flat-to-tree | failed | 2/4 | 21015 | 18 | stop |
| paginate-and-sort | passed | 4/4 | 27486 | 18 | stop |
| deep-merge | passed | 4/4 | 14200 | 19 | stop |
| csv-parse | runtime_error | 0/4 | 30246 | 19 | stop |
| render-template | passed | 4/4 | 23348 | 18 | stop |
| shopping-cart | passed | 4/4 | 22492 | 18 | stop |
| query-string-parser | failed | 3/5 | 35399 | 19 | stop |
| schema-validator | failed | 2/4 | 24039 | 19 | stop |
| state-reducer | passed | 4/4 | 35810 | 19 | stop |
| rbac-checker | passed | 3/3 | 20192 | 18 | stop |
| i18n-pluralize | passed | 3/3 | 18370 | 18 | stop |
| sql-query-builder | compile_error | 0/3 | 119069 | 18 | stop |
| json-schema-deref-validate | failed | 1/3 | 67199 | 19 | stop |
| cron-next-runs | runtime_error | 0/3 | 73205 | 19 | stop |
| longest-substring-no-repeat | failed | 1/5 | 7766 | 19 | stop |
| group-anagrams | passed | 5/5 | 9792 | 19 | stop |
| top-k-frequent | passed | 5/5 | 10923 | 19 | stop |
| merge-intervals | passed | 6/6 | 12879 | 19 | stop |
| flatten-tree | passed | 4/4 | 6123 | 17 | stop |
| shortest-path-grid | passed | 4/4 | 23602 | 20 | stop |
| lcs-length | passed | 5/5 | 10591 | 19 | stop |
| topological-sort | passed | 5/5 | 14172 | 19 | stop |
| rotate-square-matrix | runtime_error | 2/4 | 6643 | 18 | stop |
| validate-sudoku-board | passed | 4/4 | 21943 | 19 | stop |
| deep-equal | passed | 8/8 | 15463 | 19 | stop |
| bytecode-vm-evolution | runtime_error | 3/6 | 70579 | 18 | stop |
| event-emitter-evolution | failed | 1/3 | 36578 | 18 | stop |

## Failure details

- `flat-to-tree`: failed
- `csv-parse`: runtime_error — not a function
- `query-string-parser`: failed
- `schema-validator`: failed
- `sql-query-builder`: compile_error — invalid redefinition of global identifier in module code
- `json-schema-deref-validate`: failed
- `cron-next-runs`: runtime_error — Failed to find next valid time after from
- `longest-substring-no-repeat`: failed
- `rotate-square-matrix`: runtime_error — cannot read property 'length' of undefined
- `bytecode-vm-evolution`: runtime_error — Division by zero at line 3
- `event-emitter-evolution`: failed
