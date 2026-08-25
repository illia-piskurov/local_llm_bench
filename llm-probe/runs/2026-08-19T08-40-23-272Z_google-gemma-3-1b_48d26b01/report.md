# llm-probe benchmark report

| | |
|---|---|
| **Run** | `2026-08-19T08-40-23-272Z_google-gemma-3-1b_48d26b01` |
| **Status** | completed |
| **Model** | `google/gemma-3-1b` |
| **Hardware** | AMD Ryzen 7 7735HS | 32GB 5600 | 680m Radeon |
| **Started** | 2026-08-19T08:40:23.272Z |
| **Completed** | 2026-08-19T08:42:42.163Z |
| **Samples (k)** | 1 |
| **Tasks** | 27 |

## Accuracy

| Metric | Value |
|---|---|
| **success@1 (0-shot)** | 1/27 (4%) |

## Accuracy by category

| Category | Pass rate | Tasks |
|---|---|---|
| **product** | 0/14 (0%) | 14 |
| **strings** | 0/1 (0%) | 1 |
| **collections** | 0/2 (0%) | 2 |
| **numbers** | 0/1 (0%) | 1 |
| **structures** | 0/1 (0%) | 1 |
| **algorithms** | 0/3 (0%) | 3 |
| **correctness** | 1/3 (33%) | 3 |
| **evolution** | 0/2 (0%) | 2 |

## Latency & throughput

| | |
|---|---|
| Mean generation | 5054 ms |
| Median generation | 4393 ms |
| Min / Max | 1490 ms / 17836 ms |
| Mean tok/s | **42** tok/s |
| Total completion tokens | 5965 (221 tok/task) |
| **Quality/Speed Score** | **5.8** |

## Failure breakdown

| Failure type | Count |
|---|---|
| failed | 17 |
| runtime_error | 6 |
| compile_error | 2 |
| invalid_output | 1 |

## Results by task

| Task | Status | Tests | Gen ms | tok/s | Finish |
|---|---|---|---|---|---|
| flat-to-tree | failed | 1/4 | 1535 | 32 | stop |
| paginate-and-sort | failed | 0/4 | 6987 | 44 | stop |
| deep-merge | runtime_error | 1/4 | 2918 | 42 | stop |
| csv-parse | runtime_error | 0/4 | 4056 | 43 | stop |
| render-template | failed | 2/4 | 3218 | 40 | stop |
| shopping-cart | compile_error | 0/4 | 7187 | 43 | stop |
| query-string-parser | compile_error | 0/5 | 5409 | 44 | stop |
| schema-validator | failed | 1/4 | 6583 | 44 | stop |
| state-reducer | failed | 1/4 | 6946 | 44 | stop |
| rbac-checker | failed | 1/3 | 5229 | 42 | stop |
| i18n-pluralize | invalid_output | 0/3 | 3701 | 41 | stop |
| sql-query-builder | failed | 1/3 | 4537 | 38 | stop |
| json-schema-deref-validate | failed | 0/3 | 4393 | 41 | stop |
| cron-next-runs | runtime_error | 0/3 | 7707 | 44 | stop |
| longest-substring-no-repeat | failed | 1/5 | 2889 | 44 | stop |
| group-anagrams | failed | 1/5 | 2934 | 44 | stop |
| top-k-frequent | failed | 0/5 | 2979 | 43 | stop |
| merge-intervals | failed | 3/6 | 2511 | 43 | stop |
| flatten-tree | failed | 3/4 | 3049 | 44 | stop |
| shortest-path-grid | runtime_error | 0/4 | 6793 | 47 | stop |
| lcs-length | failed | 2/5 | 4726 | 46 | stop |
| topological-sort | failed | 3/5 | 7189 | 46 | stop |
| rotate-square-matrix | runtime_error | 0/4 | 1490 | 35 | stop |
| validate-sudoku-board | passed | 4/4 | 8452 | 47 | stop |
| deep-equal | failed | 5/8 | 2909 | 41 | stop |
| bytecode-vm-evolution | failed | 0/6 | 17836 | 47 | stop |
| event-emitter-evolution | runtime_error | 0/3 | 2303 | 33 | stop |

## Failure details

- `flat-to-tree`: failed
- `paginate-and-sort`: failed
- `deep-merge`: runtime_error — cannot read property 'Symbol.iterator' of undefined
- `csv-parse`: runtime_error — not a function
- `render-template`: failed
- `shopping-cart`: compile_error — invalid redefinition of lexical identifier
- `query-string-parser`: compile_error — expecting ','
- `schema-validator`: failed
- `state-reducer`: failed
- `rbac-checker`: failed
- `i18n-pluralize`: invalid_output — Test plural-forms returned a non-JSON value
- `sql-query-builder`: failed
- `json-schema-deref-validate`: failed
- `cron-next-runs`: runtime_error — not a function
- `longest-substring-no-repeat`: failed
- `group-anagrams`: failed
- `top-k-frequent`: failed
- `merge-intervals`: failed
- `flatten-tree`: failed
- `shortest-path-grid`: runtime_error — cannot read property of undefined
- `lcs-length`: failed
- `topological-sort`: failed
- `rotate-square-matrix`: runtime_error — value is not iterable
- `deep-equal`: failed
- `bytecode-vm-evolution`: failed
- `event-emitter-evolution`: runtime_error — value is not iterable
