# llm-probe benchmark report

| | |
|---|---|
| **Run** | `2026-08-18T15-50-34-146Z_ibm-granite-4-h-tiny_a0fedb6a` |
| **Status** | completed |
| **Model** | `ibm/granite-4-h-tiny` |
| **Hardware** | AMD RYZEN 7 250 | 32 GB 5600 | 780m Radeon |
| **Started** | 2026-08-18T15:50:34.146Z |
| **Completed** | 2026-08-18T15:55:55.052Z |
| **Samples (k)** | 1 |
| **Tasks** | 27 |

## Accuracy

| Metric | Value |
|---|---|
| **success@1 (0-shot)** | 11/27 (41%) |

## Accuracy by category

| Category | Pass rate | Tasks |
|---|---|---|
| **product** | 4/14 (29%) | 14 |
| **strings** | 1/1 (100%) | 1 |
| **collections** | 1/2 (50%) | 2 |
| **numbers** | 1/1 (100%) | 1 |
| **structures** | 1/1 (100%) | 1 |
| **algorithms** | 3/3 (100%) | 3 |
| **correctness** | 0/3 (0%) | 3 |
| **evolution** | 0/2 (0%) | 2 |

## Latency & throughput

| | |
|---|---|
| Mean generation | 11786 ms |
| Median generation | 7542 ms |
| Min / Max | 3723 ms / 54228 ms |
| Mean tok/s | **28** tok/s |
| Total completion tokens | 8992 (333 tok/task) |
| **Quality/Speed Score** | **49.9** |

## Failure breakdown

| Failure type | Count |
|---|---|
| failed | 8 |
| runtime_error | 6 |
| extract_error | 1 |
| compile_error | 1 |

## Results by task

| Task | Status | Tests | Gen ms | tok/s | Finish |
|---|---|---|---|---|---|
| flat-to-tree | failed | 1/4 | 5233 | 25 | stop |
| paginate-and-sort | passed | 4/4 | 14237 | 32 | stop |
| deep-merge | passed | 4/4 | 5440 | 25 | stop |
| csv-parse | runtime_error | 0/4 | 5916 | 27 | stop |
| render-template | failed | 3/4 | 6914 | 27 | stop |
| shopping-cart | passed | 4/4 | 10001 | 28 | stop |
| query-string-parser | runtime_error | 1/5 | 11615 | 30 | stop |
| schema-validator | failed | 2/4 | 17214 | 30 | stop |
| state-reducer | passed | 4/4 | 17682 | 30 | stop |
| rbac-checker | runtime_error | 0/3 | 8561 | 28 | stop |
| i18n-pluralize | failed | 1/3 | 7286 | 27 | stop |
| sql-query-builder | runtime_error | 0/3 | 24644 | 33 | stop |
| json-schema-deref-validate | extract_error | 0/0 | 24040 | — | stop |
| cron-next-runs | compile_error | 0/3 | 54228 | 35 | stop |
| longest-substring-no-repeat | passed | 5/5 | 4843 | 25 | stop |
| group-anagrams | failed | 4/5 | 4309 | 24 | stop |
| top-k-frequent | passed | 5/5 | 4963 | 25 | stop |
| merge-intervals | passed | 6/6 | 4709 | 24 | stop |
| flatten-tree | passed | 4/4 | 3723 | 21 | stop |
| shortest-path-grid | passed | 4/4 | 9287 | 31 | stop |
| lcs-length | passed | 5/5 | 6433 | 29 | stop |
| topological-sort | passed | 5/5 | 6697 | 29 | stop |
| rotate-square-matrix | failed | 2/4 | 6320 | 28 | stop |
| validate-sudoku-board | failed | 3/4 | 8054 | 30 | stop |
| deep-equal | runtime_error | 3/8 | 7542 | 30 | stop |
| bytecode-vm-evolution | runtime_error | 2/6 | 30738 | 34 | stop |
| event-emitter-evolution | failed | 0/3 | 7595 | 27 | stop |

## Failure details

- `flat-to-tree`: failed
- `csv-parse`: runtime_error — not a function
- `render-template`: failed
- `query-string-parser`: runtime_error — not a function
- `schema-validator`: failed
- `rbac-checker`: runtime_error — cannot read property 'Symbol.iterator' of undefined
- `i18n-pluralize`: failed
- `sql-query-builder`: runtime_error — 'params' is not defined
- `json-schema-deref-validate`: extract_error — Response did not contain export function solve(input)
- `cron-next-runs`: compile_error — unexpected token in expression: 'else'
- `group-anagrams`: failed
- `rotate-square-matrix`: failed
- `validate-sudoku-board`: failed
- `deep-equal`: runtime_error — cannot convert to object
- `bytecode-vm-evolution`: runtime_error — Stack underflow at line 2
- `event-emitter-evolution`: failed
