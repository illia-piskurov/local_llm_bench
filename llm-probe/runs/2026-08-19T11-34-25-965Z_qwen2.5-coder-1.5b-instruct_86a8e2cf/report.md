# llm-probe benchmark report

| | |
|---|---|
| **Run** | `2026-08-19T11-34-25-965Z_qwen2.5-coder-1.5b-instruct_86a8e2cf` |
| **Status** | completed |
| **Model** | `qwen2.5-coder-1.5b-instruct` |
| **Hardware** | AMD Ryzen 7 7735HS | 32GB 5600 | 680m Radeon |
| **Started** | 2026-08-19T11:34:25.965Z |
| **Completed** | 2026-08-19T11:39:46.485Z |
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
| **numbers** | 0/1 (0%) | 1 |
| **structures** | 0/1 (0%) | 1 |
| **algorithms** | 1/3 (33%) | 3 |
| **correctness** | 1/3 (33%) | 3 |
| **evolution** | 0/2 (0%) | 2 |

## Latency & throughput

| | |
|---|---|
| Mean generation | 11774 ms |
| Median generation | 9364 ms |
| Min / Max | 1137 ms / 37554 ms |
| Mean tok/s | **26** tok/s |
| Total completion tokens | 7183 (266 tok/task) |
| **Quality/Speed Score** | **8.7** |

## Failure breakdown

| Failure type | Count |
|---|---|
| failed | 12 |
| runtime_error | 8 |
| compile_error | 4 |
| extract_error | 1 |

## Results by task

| Task | Status | Tests | Gen ms | tok/s | Finish |
|---|---|---|---|---|---|
| flat-to-tree | failed | 1/4 | 4387 | 27 | stop |
| paginate-and-sort | failed | 3/4 | 12478 | 28 | stop |
| deep-merge | failed | 3/4 | 5637 | 28 | stop |
| csv-parse | runtime_error | 0/4 | 4957 | 27 | stop |
| render-template | failed | 2/4 | 6725 | 29 | stop |
| shopping-cart | runtime_error | 0/4 | 9364 | 28 | stop |
| query-string-parser | runtime_error | 1/5 | 10209 | 28 | stop |
| schema-validator | runtime_error | 3/4 | 28055 | 17 | stop |
| state-reducer | compile_error | 0/4 | 37554 | 16 | stop |
| rbac-checker | failed | 1/3 | 13471 | 12 | stop |
| i18n-pluralize | runtime_error | 0/3 | 14661 | 15 | stop |
| sql-query-builder | failed | 0/3 | 19291 | 29 | stop |
| json-schema-deref-validate | extract_error | 0/0 | 20459 | — | stop |
| cron-next-runs | runtime_error | 0/3 | 21331 | 28 | stop |
| longest-substring-no-repeat | compile_error | 0/5 | 9615 | 30 | stop |
| group-anagrams | failed | 4/5 | 3228 | 26 | stop |
| top-k-frequent | failed | 0/5 | 3647 | 28 | stop |
| merge-intervals | failed | 5/6 | 4836 | 28 | stop |
| flatten-tree | compile_error | 0/4 | 3455 | 25 | stop |
| shortest-path-grid | runtime_error | 0/4 | 8117 | 29 | stop |
| lcs-length | passed | 5/5 | 6212 | 28 | stop |
| topological-sort | failed | 4/5 | 6795 | 27 | stop |
| rotate-square-matrix | failed | 2/4 | 1137 | 21 | stop |
| validate-sudoku-board | failed | 3/4 | 13035 | 29 | stop |
| deep-equal | passed | 8/8 | 7301 | 28 | stop |
| bytecode-vm-evolution | compile_error | 0/6 | 28510 | 28 | stop |
| event-emitter-evolution | runtime_error | 0/3 | 13428 | 28 | stop |

## Failure details

- `flat-to-tree`: failed
- `paginate-and-sort`: failed
- `deep-merge`: failed
- `csv-parse`: runtime_error — not a function
- `render-template`: failed
- `shopping-cart`: runtime_error — 'discount' is not defined
- `query-string-parser`: runtime_error — 'value' is read-only
- `schema-validator`: runtime_error — cannot read property 'push' of undefined
- `state-reducer`: compile_error — invalid redefinition of lexical identifier
- `rbac-checker`: failed
- `i18n-pluralize`: runtime_error — 'text' is not defined
- `sql-query-builder`: failed
- `json-schema-deref-validate`: extract_error — Response did not contain export function solve(input)
- `cron-next-runs`: runtime_error — Invalid cron syntax
- `longest-substring-no-repeat`: compile_error — expecting ';'
- `group-anagrams`: failed
- `top-k-frequent`: failed
- `merge-intervals`: failed
- `flatten-tree`: compile_error — not a function
- `shortest-path-grid`: runtime_error — cannot read property of undefined
- `topological-sort`: failed
- `rotate-square-matrix`: failed
- `validate-sudoku-board`: failed
- `bytecode-vm-evolution`: compile_error — invalid redefinition of lexical identifier
- `event-emitter-evolution`: runtime_error — 'listeners' is not defined
