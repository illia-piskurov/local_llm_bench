# llm-probe benchmark report

| | |
|---|---|
| **Run** | `2026-08-18T15-00-58-758Z_mistralai-ministral-3-3b_1fe0576c` |
| **Status** | completed |
| **Model** | `mistralai/ministral-3-3b` |
| **Hardware** | AMD RYZEN 7 250 | 32 GB 5600 | 780m Radeon |
| **Started** | 2026-08-18T15:00:58.758Z |
| **Completed** | 2026-08-18T15:09:28.685Z |
| **Samples (k)** | 1 |
| **Tasks** | 27 |

## Accuracy

| Metric | Value |
|---|---|
| **success@1 (0-shot)** | 10/27 (37%) |

## Accuracy by category

| Category | Pass rate | Tasks |
|---|---|---|
| **product** | 3/14 (21%) | 14 |
| **strings** | 0/1 (0%) | 1 |
| **collections** | 1/2 (50%) | 2 |
| **numbers** | 1/1 (100%) | 1 |
| **structures** | 1/1 (100%) | 1 |
| **algorithms** | 3/3 (100%) | 3 |
| **correctness** | 1/3 (33%) | 3 |
| **evolution** | 0/2 (0%) | 2 |

## Latency & throughput

| | |
|---|---|
| Mean generation | 18756 ms |
| Median generation | 14548 ms |
| Min / Max | 2405 ms / 63948 ms |
| Mean tok/s | **18** tok/s |
| Total completion tokens | 9087 (337 tok/task) |
| **Quality/Speed Score** | **34.8** |

## Failure breakdown

| Failure type | Count |
|---|---|
| failed | 14 |
| runtime_error | 2 |
| timeout | 1 |

## Results by task

| Task | Status | Tests | Gen ms | tok/s | Finish |
|---|---|---|---|---|---|
| flat-to-tree | failed | 1/4 | 9786 | 23 | stop |
| paginate-and-sort | passed | 4/4 | 25219 | 20 | stop |
| deep-merge | failed | 3/4 | 22055 | 17 | stop |
| csv-parse | failed | 2/4 | 12180 | 17 | stop |
| render-template | failed | 2/4 | 7970 | 20 | stop |
| shopping-cart | passed | 4/4 | 20832 | 20 | stop |
| query-string-parser | failed | 2/5 | 19756 | 18 | stop |
| schema-validator | failed | 2/4 | 27772 | 19 | stop |
| state-reducer | failed | 3/4 | 28361 | 20 | stop |
| rbac-checker | passed | 3/3 | 22219 | 18 | stop |
| i18n-pluralize | failed | 2/3 | 11004 | 18 | stop |
| sql-query-builder | runtime_error | 0/3 | 35191 | 18 | stop |
| json-schema-deref-validate | runtime_error | 0/3 | 38294 | 20 | stop |
| cron-next-runs | timeout | 0/3 | 27734 | 19 | stop |
| longest-substring-no-repeat | failed | 1/5 | 6557 | 18 | stop |
| group-anagrams | failed | 4/5 | 5728 | 19 | stop |
| top-k-frequent | passed | 5/5 | 5707 | 20 | stop |
| merge-intervals | passed | 6/6 | 7930 | 19 | stop |
| flatten-tree | passed | 4/4 | 4756 | 18 | stop |
| shortest-path-grid | passed | 4/4 | 13867 | 21 | stop |
| lcs-length | passed | 5/5 | 9239 | 19 | stop |
| topological-sort | passed | 5/5 | 10683 | 19 | stop |
| rotate-square-matrix | failed | 2/4 | 2405 | 15 | stop |
| validate-sudoku-board | failed | 3/4 | 21787 | 15 | stop |
| deep-equal | passed | 8/8 | 14548 | 15 | stop |
| bytecode-vm-evolution | failed | 4/6 | 63948 | 14 | stop |
| event-emitter-evolution | failed | 0/3 | 30894 | 15 | stop |

## Failure details

- `flat-to-tree`: failed
- `deep-merge`: failed
- `csv-parse`: failed
- `render-template`: failed
- `query-string-parser`: failed
- `schema-validator`: failed
- `state-reducer`: failed
- `i18n-pluralize`: failed
- `sql-query-builder`: runtime_error — cannot read property 'map' of undefined
- `json-schema-deref-validate`: runtime_error — 'definitions' is not defined
- `cron-next-runs`: timeout — interrupted
- `longest-substring-no-repeat`: failed
- `group-anagrams`: failed
- `rotate-square-matrix`: failed
- `validate-sudoku-board`: failed
- `bytecode-vm-evolution`: failed
- `event-emitter-evolution`: failed
