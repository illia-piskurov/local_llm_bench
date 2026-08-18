# llm-probe benchmark report

| | |
|---|---|
| **Run** | `2026-08-18T19-04-54-866Z_google-gemma-4-e4b_55efddad` |
| **Status** | completed |
| **Model** | `google/gemma-4-e4b` |
| **Hardware** | AMD RYZEN 7 250 | 32 GB 5600 | 780m Radeon |
| **Started** | 2026-08-18T19:04:54.866Z |
| **Completed** | 2026-08-18T19:55:38.499Z |
| **Samples (k)** | 1 |
| **Tasks** | 27 |

## Accuracy

| Metric | Value |
|---|---|
| **success@1 (0-shot)** | 19/27 (70%) |

## Accuracy by category

| Category | Pass rate | Tasks |
|---|---|---|
| **product** | 7/14 (50%) | 14 |
| **strings** | 1/1 (100%) | 1 |
| **collections** | 2/2 (100%) | 2 |
| **numbers** | 1/1 (100%) | 1 |
| **structures** | 0/1 (0%) | 1 |
| **algorithms** | 3/3 (100%) | 3 |
| **correctness** | 3/3 (100%) | 3 |
| **evolution** | 2/2 (100%) | 2 |

## Latency & throughput

| | |
|---|---|
| Mean generation | 112637 ms |
| Median generation | 114311 ms |
| Min / Max | 8688 ms / 277427 ms |
| Mean tok/s | **18** tok/s |
| Total completion tokens | 53702 (1989 tok/task) |
| **Quality/Speed Score** | **66.1** |

## Failure breakdown

| Failure type | Count |
|---|---|
| failed | 5 |
| compile_error | 2 |
| timeout | 1 |

## Results by task

| Task | Status | Tests | Gen ms | tok/s | Finish |
|---|---|---|---|---|---|
| flat-to-tree | passed | 4/4 | 146372 | 14 | stop |
| paginate-and-sort | passed | 4/4 | 191951 | 14 | stop |
| deep-merge | passed | 4/4 | 57442 | 18 | stop |
| csv-parse | timeout | 1/4 | 158288 | 18 | stop |
| render-template | failed | 2/4 | 143033 | 18 | stop |
| shopping-cart | passed | 4/4 | 83199 | 18 | stop |
| query-string-parser | failed | 4/5 | 159435 | 18 | stop |
| schema-validator | failed | 2/4 | 114311 | 18 | stop |
| state-reducer | compile_error | 0/4 | 277427 | 18 | stop |
| rbac-checker | passed | 3/3 | 126565 | 18 | stop |
| i18n-pluralize | passed | 3/3 | 121602 | 18 | stop |
| sql-query-builder | passed | 3/3 | 148181 | 18 | stop |
| json-schema-deref-validate | failed | 1/3 | 140180 | 18 | stop |
| cron-next-runs | compile_error | 0/3 | 140332 | 18 | stop |
| longest-substring-no-repeat | passed | 5/5 | 107386 | 18 | stop |
| group-anagrams | passed | 5/5 | 75434 | 18 | stop |
| top-k-frequent | passed | 5/5 | 79373 | 18 | stop |
| merge-intervals | passed | 6/6 | 23746 | 18 | stop |
| flatten-tree | failed | 0/4 | 8688 | 17 | stop |
| shortest-path-grid | passed | 4/4 | 90839 | 18 | stop |
| lcs-length | passed | 5/5 | 18760 | 18 | stop |
| topological-sort | passed | 5/5 | 73605 | 18 | stop |
| rotate-square-matrix | passed | 4/4 | 24311 | 18 | stop |
| validate-sudoku-board | passed | 4/4 | 105136 | 18 | stop |
| deep-equal | passed | 8/8 | 58499 | 18 | stop |
| bytecode-vm-evolution | passed | 6/6 | 227929 | 18 | stop |
| event-emitter-evolution | passed | 3/3 | 139169 | 18 | stop |

## Failure details

- `csv-parse`: timeout — interrupted
- `render-template`: failed
- `query-string-parser`: failed
- `schema-validator`: failed
- `state-reducer`: compile_error — unexpected token in expression: 'catch'
- `json-schema-deref-validate`: failed
- `cron-next-runs`: compile_error — unexpected token in expression: '*'
- `flatten-tree`: failed
