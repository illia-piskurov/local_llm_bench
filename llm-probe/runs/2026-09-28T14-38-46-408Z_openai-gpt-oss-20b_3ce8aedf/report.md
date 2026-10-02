# llm-probe benchmark report

| | |
|---|---|
| **Run** | `2026-09-28T14-38-46-408Z_openai-gpt-oss-20b_3ce8aedf` |
| **Status** | completed |
| **Model** | `openai/gpt-oss-20b` |
| **Hardware** | M4 | 24GB | 10-core GPU M4 |
| **Started** | 2026-09-28T14:38:46.408Z |
| **Completed** | 2026-09-28T14:47:47.306Z |
| **Samples (k)** | 1 |
| **Tasks** | 27 |

## Accuracy

| Metric | Value |
|---|---|
| **success@1 (0-shot)** | 23/27 (85%) |

## Accuracy by category

| Category | Pass rate | Tasks |
|---|---|---|
| **product** | 10/14 (71%) | 14 |
| **strings** | 1/1 (100%) | 1 |
| **collections** | 2/2 (100%) | 2 |
| **numbers** | 1/1 (100%) | 1 |
| **structures** | 1/1 (100%) | 1 |
| **algorithms** | 3/3 (100%) | 3 |
| **correctness** | 3/3 (100%) | 3 |
| **evolution** | 2/2 (100%) | 2 |

## Latency & throughput

| | |
|---|---|
| Mean generation | 19975 ms |
| Median generation | 17630 ms |
| Min / Max | 5853 ms / 47627 ms |
| Mean tok/s | **24** tok/s |
| Total completion tokens | 12919 (478 tok/task) |
| **Quality/Speed Score** | **95** |

## Failure breakdown

| Failure type | Count |
|---|---|
| failed | 3 |
| compile_error | 1 |

## Results by task

| Task | Status | Tests | Gen ms | tok/s | Finish |
|---|---|---|---|---|---|
| flat-to-tree | passed | 4/4 | 17456 | 23 | stop |
| paginate-and-sort | passed | 4/4 | 15503 | 30 | stop |
| deep-merge | passed | 4/4 | 8207 | 29 | stop |
| csv-parse | failed | 2/4 | 24009 | 31 | stop |
| render-template | passed | 4/4 | 9121 | 28 | stop |
| shopping-cart | passed | 4/4 | 20504 | 28 | stop |
| query-string-parser | failed | 3/5 | 36709 | 24 | stop |
| schema-validator | passed | 4/4 | 29675 | 23 | stop |
| state-reducer | passed | 4/4 | 28547 | 23 | stop |
| rbac-checker | passed | 3/3 | 19615 | 22 | stop |
| i18n-pluralize | compile_error | 0/3 | 19924 | 22 | stop |
| sql-query-builder | passed | 3/3 | 34255 | 21 | stop |
| json-schema-deref-validate | failed | 2/3 | 45367 | 24 | stop |
| cron-next-runs | passed | 3/3 | 39515 | 26 | stop |
| longest-substring-no-repeat | passed | 5/5 | 6504 | 22 | stop |
| group-anagrams | passed | 5/5 | 8693 | 24 | stop |
| top-k-frequent | passed | 5/5 | 8530 | 24 | stop |
| merge-intervals | passed | 6/6 | 8483 | 23 | stop |
| flatten-tree | passed | 4/4 | 5853 | 21 | stop |
| shortest-path-grid | passed | 4/4 | 17630 | 22 | stop |
| lcs-length | passed | 5/5 | 10617 | 23 | stop |
| topological-sort | passed | 5/5 | 11752 | 23 | stop |
| rotate-square-matrix | passed | 4/4 | 7267 | 21 | stop |
| validate-sudoku-board | passed | 4/4 | 15699 | 22 | stop |
| deep-equal | passed | 8/8 | 20415 | 23 | stop |
| bytecode-vm-evolution | passed | 6/6 | 47627 | 23 | stop |
| event-emitter-evolution | passed | 3/3 | 21836 | 23 | stop |

## Failure details

- `csv-parse`: failed
- `query-string-parser`: failed
- `i18n-pluralize`: compile_error — unexpected token in expression: '<'
- `json-schema-deref-validate`: failed
