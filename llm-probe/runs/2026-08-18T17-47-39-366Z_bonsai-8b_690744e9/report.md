# llm-probe benchmark report

| | |
|---|---|
| **Run** | `2026-08-18T17-47-39-366Z_bonsai-8b_690744e9` |
| **Status** | completed |
| **Model** | `bonsai-8b` |
| **Hardware** | AMD RYZEN 7 250 | 32 GB 5600 | 780m Radeon |
| **Started** | 2026-08-18T17:47:39.366Z |
| **Completed** | 2026-08-18T17:55:00.409Z |
| **Samples (k)** | 1 |
| **Tasks** | 27 |

## Accuracy

| Metric | Value |
|---|---|
| **success@1 (0-shot)** | 2/27 (7%) |

## Accuracy by category

| Category | Pass rate | Tasks |
|---|---|---|
| **product** | 0/14 (0%) | 14 |
| **strings** | 0/1 (0%) | 1 |
| **collections** | 0/2 (0%) | 2 |
| **numbers** | 1/1 (100%) | 1 |
| **structures** | 0/1 (0%) | 1 |
| **algorithms** | 1/3 (33%) | 3 |
| **correctness** | 0/3 (0%) | 3 |
| **evolution** | 0/2 (0%) | 2 |

## Latency & throughput

| | |
|---|---|
| Mean generation | 16254 ms |
| Median generation | 14535 ms |
| Min / Max | 3938 ms / 59587 ms |
| Mean tok/s | **24** tok/s |
| Total completion tokens | 10032 (372 tok/task) |
| **Quality/Speed Score** | **8.3** |

## Failure breakdown

| Failure type | Count |
|---|---|
| failed | 11 |
| runtime_error | 10 |
| compile_error | 3 |
| extract_error | 1 |

## Results by task

| Task | Status | Tests | Gen ms | tok/s | Finish |
|---|---|---|---|---|---|
| flat-to-tree | runtime_error | 0/4 | 7011 | 27 | stop |
| paginate-and-sort | failed | 2/4 | 18219 | 27 | stop |
| deep-merge | failed | 2/4 | 6568 | 25 | stop |
| csv-parse | compile_error | 0/4 | 9559 | 26 | stop |
| render-template | failed | 2/4 | 8059 | 25 | stop |
| shopping-cart | failed | 1/4 | 15583 | 25 | stop |
| query-string-parser | runtime_error | 0/5 | 16322 | 25 | stop |
| schema-validator | failed | 0/4 | 23723 | 25 | stop |
| state-reducer | compile_error | 0/4 | 21253 | 24 | stop |
| rbac-checker | runtime_error | 0/3 | 20716 | 23 | stop |
| i18n-pluralize | runtime_error | 0/3 | 14798 | 23 | stop |
| sql-query-builder | runtime_error | 0/3 | 21496 | 23 | stop |
| json-schema-deref-validate | failed | 0/3 | 59587 | 23 | stop |
| cron-next-runs | runtime_error | 0/3 | 33738 | 23 | stop |
| longest-substring-no-repeat | failed | 0/5 | 5001 | 23 | stop |
| group-anagrams | runtime_error | 0/5 | 5957 | 23 | stop |
| top-k-frequent | failed | 0/5 | 6235 | 23 | stop |
| merge-intervals | passed | 6/6 | 8151 | 23 | stop |
| flatten-tree | runtime_error | 1/4 | 4734 | 22 | stop |
| shortest-path-grid | failed | 0/4 | 18322 | 24 | stop |
| lcs-length | extract_error | 0/0 | 7624 | — | stop |
| topological-sort | passed | 5/5 | 10399 | 23 | stop |
| rotate-square-matrix | runtime_error | 0/4 | 3938 | 22 | stop |
| validate-sudoku-board | failed | 3/4 | 24099 | 14 | stop |
| deep-equal | runtime_error | 5/8 | 7685 | 25 | stop |
| bytecode-vm-evolution | compile_error | 0/6 | 45543 | 23 | stop |
| event-emitter-evolution | failed | 0/3 | 14535 | 22 | stop |

## Failure details

- `flat-to-tree`: runtime_error — 'entries' is not defined
- `paginate-and-sort`: failed
- `deep-merge`: failed
- `csv-parse`: compile_error — expecting '}'
- `render-template`: failed
- `shopping-cart`: failed
- `query-string-parser`: runtime_error — 'value' is read-only
- `schema-validator`: failed
- `state-reducer`: compile_error — cannot delete a direct reference in strict mode
- `rbac-checker`: runtime_error — not a function
- `i18n-pluralize`: runtime_error — not a function
- `sql-query-builder`: runtime_error — cannot read property 'join' of undefined
- `json-schema-deref-validate`: failed
- `cron-next-runs`: runtime_error — not a function
- `longest-substring-no-repeat`: failed
- `group-anagrams`: runtime_error — not a function
- `top-k-frequent`: failed
- `flatten-tree`: runtime_error — cannot read property 'left' of null
- `shortest-path-grid`: failed
- `lcs-length`: extract_error — Response did not contain export function solve(input)
- `rotate-square-matrix`: runtime_error — cannot read property of undefined
- `validate-sudoku-board`: failed
- `deep-equal`: runtime_error — cannot convert to object
- `bytecode-vm-evolution`: compile_error — invalid redefinition of lexical identifier
- `event-emitter-evolution`: failed
