# llm-probe benchmark report

| | |
|---|---|
| **Run** | `2026-08-19T11-41-11-937Z_qwen2.5-coder-3b-instruct_2d739f2e` |
| **Status** | completed |
| **Model** | `qwen2.5-coder-3b-instruct` |
| **Hardware** | AMD Ryzen 7 7735HS | 32GB 5600 | 680m Radeon |
| **Started** | 2026-08-19T11:41:11.937Z |
| **Completed** | 2026-08-19T11:48:22.160Z |
| **Samples (k)** | 1 |
| **Tasks** | 27 |

## Accuracy

| Metric | Value |
|---|---|
| **success@1 (0-shot)** | 11/27 (41%) |

## Accuracy by category

| Category | Pass rate | Tasks |
|---|---|---|
| **product** | 3/14 (21%) | 14 |
| **strings** | 1/1 (100%) | 1 |
| **collections** | 2/2 (100%) | 2 |
| **numbers** | 1/1 (100%) | 1 |
| **structures** | 1/1 (100%) | 1 |
| **algorithms** | 2/3 (67%) | 3 |
| **correctness** | 1/3 (33%) | 3 |
| **evolution** | 0/2 (0%) | 2 |

## Latency & throughput

| | |
|---|---|
| Mean generation | 15828 ms |
| Median generation | 12467 ms |
| Min / Max | 4267 ms / 46156 ms |
| Mean tok/s | **22** tok/s |
| Total completion tokens | 8809 (326 tok/task) |
| **Quality/Speed Score** | **43.1** |

## Failure breakdown

| Failure type | Count |
|---|---|
| failed | 7 |
| runtime_error | 7 |
| extract_error | 1 |
| compile_error | 1 |

## Results by task

| Task | Status | Tests | Gen ms | tok/s | Finish |
|---|---|---|---|---|---|
| flat-to-tree | failed | 1/4 | 9569 | 21 | stop |
| paginate-and-sort | passed | 4/4 | 17094 | 22 | stop |
| deep-merge | passed | 4/4 | 7294 | 22 | stop |
| csv-parse | failed | 3/4 | 11443 | 23 | stop |
| render-template | failed | 3/4 | 11337 | 22 | stop |
| shopping-cart | failed | 3/4 | 18520 | 22 | stop |
| query-string-parser | failed | 3/5 | 12742 | 21 | stop |
| schema-validator | failed | 2/4 | 19899 | 23 | stop |
| state-reducer | failed | 3/4 | 30212 | 24 | stop |
| rbac-checker | runtime_error | 1/3 | 12946 | 22 | stop |
| i18n-pluralize | passed | 3/3 | 12634 | 22 | stop |
| sql-query-builder | runtime_error | 0/3 | 28580 | 23 | stop |
| json-schema-deref-validate | runtime_error | 0/3 | 30695 | 24 | stop |
| cron-next-runs | extract_error | 0/0 | 22654 | — | stop |
| longest-substring-no-repeat | passed | 5/5 | 9223 | 24 | stop |
| group-anagrams | passed | 5/5 | 5769 | 23 | stop |
| top-k-frequent | passed | 5/5 | 12467 | 24 | stop |
| merge-intervals | passed | 6/6 | 8953 | 23 | stop |
| flatten-tree | passed | 4/4 | 4267 | 20 | stop |
| shortest-path-grid | passed | 4/4 | 14056 | 24 | stop |
| lcs-length | runtime_error | 1/5 | 8386 | 24 | stop |
| topological-sort | passed | 5/5 | 10304 | 23 | stop |
| rotate-square-matrix | runtime_error | 2/4 | 6334 | 22 | stop |
| validate-sudoku-board | passed | 4/4 | 11959 | 23 | stop |
| deep-equal | runtime_error | 1/8 | 5523 | 22 | stop |
| bytecode-vm-evolution | compile_error | 0/6 | 46156 | 23 | stop |
| event-emitter-evolution | runtime_error | 0/3 | 38347 | 11 | stop |

## Failure details

- `flat-to-tree`: failed
- `csv-parse`: failed
- `render-template`: failed
- `shopping-cart`: failed
- `query-string-parser`: failed
- `schema-validator`: failed
- `state-reducer`: failed
- `rbac-checker`: runtime_error — nothing to repeat
- `sql-query-builder`: runtime_error — cannot read property 'length' of undefined
- `json-schema-deref-validate`: runtime_error — not a function
- `cron-next-runs`: extract_error — Response did not contain export function solve(input)
- `lcs-length`: runtime_error — cannot read property 'length' of undefined
- `rotate-square-matrix`: runtime_error — cannot read property 'length' of undefined
- `deep-equal`: runtime_error — cannot convert to object
- `bytecode-vm-evolution`: compile_error — invalid redefinition of lexical identifier
- `event-emitter-evolution`: runtime_error — value is not iterable
