# llm-probe benchmark report

| | |
|---|---|
| **Run** | `2026-08-18T16-07-58-904Z_liquid-lfm2.5-1.2b_48e61af4` |
| **Status** | completed |
| **Model** | `liquid/lfm2.5-1.2b` |
| **Hardware** | AMD RYZEN 7 250 | 32 GB 5600 | 780m Radeon |
| **Started** | 2026-08-18T16:07:58.904Z |
| **Completed** | 2026-08-18T16:10:47.971Z |
| **Samples (k)** | 1 |
| **Tasks** | 27 |

## Accuracy

| Metric | Value |
|---|---|
| **success@1 (0-shot)** | 3/27 (11%) |

## Accuracy by category

| Category | Pass rate | Tasks |
|---|---|---|
| **product** | 0/14 (0%) | 14 |
| **strings** | 0/1 (0%) | 1 |
| **collections** | 0/2 (0%) | 2 |
| **numbers** | 0/1 (0%) | 1 |
| **structures** | 0/1 (0%) | 1 |
| **algorithms** | 2/3 (67%) | 3 |
| **correctness** | 1/3 (33%) | 3 |
| **evolution** | 0/2 (0%) | 2 |

## Latency & throughput

| | |
|---|---|
| Mean generation | 6177 ms |
| Median generation | 4817 ms |
| Min / Max | 2206 ms / 18064 ms |
| Mean tok/s | **48** tok/s |
| Total completion tokens | 7996 (296 tok/task) |
| **Quality/Speed Score** | **18.8** |

## Failure breakdown

| Failure type | Count |
|---|---|
| runtime_error | 9 |
| failed | 8 |
| compile_error | 6 |
| extract_error | 1 |

## Results by task

| Task | Status | Tests | Gen ms | tok/s | Finish |
|---|---|---|---|---|---|
| flat-to-tree | runtime_error | 0/4 | 3141 | 51 | stop |
| paginate-and-sort | compile_error | 0/4 | 7229 | 50 | stop |
| deep-merge | runtime_error | 1/4 | 3057 | 46 | stop |
| csv-parse | compile_error | 0/4 | 4817 | 48 | stop |
| render-template | runtime_error | 0/4 | 5314 | 48 | stop |
| shopping-cart | runtime_error | 0/4 | 6366 | 47 | stop |
| query-string-parser | compile_error | 0/5 | 11136 | 49 | stop |
| schema-validator | failed | 0/4 | 5038 | 48 | stop |
| state-reducer | runtime_error | 0/4 | 8900 | 49 | stop |
| rbac-checker | runtime_error | 0/3 | 4674 | 46 | stop |
| i18n-pluralize | runtime_error | 0/3 | 2738 | 44 | stop |
| sql-query-builder | compile_error | 0/3 | 10825 | 48 | stop |
| json-schema-deref-validate | failed | 1/3 | 8984 | 48 | stop |
| cron-next-runs | compile_error | 0/3 | 14180 | 49 | stop |
| longest-substring-no-repeat | failed | 1/5 | 3470 | 48 | stop |
| group-anagrams | failed | 1/5 | 2962 | 47 | stop |
| top-k-frequent | runtime_error | 0/5 | 2980 | 47 | stop |
| merge-intervals | failed | 2/6 | 3308 | 48 | stop |
| flatten-tree | failed | 2/4 | 2318 | 46 | stop |
| shortest-path-grid | failed | 2/4 | 6703 | 49 | stop |
| lcs-length | passed | 5/5 | 3807 | 48 | stop |
| topological-sort | passed | 5/5 | 4805 | 48 | stop |
| rotate-square-matrix | extract_error | 0/0 | 2206 | — | stop |
| validate-sudoku-board | passed | 4/4 | 5604 | 49 | stop |
| deep-equal | failed | 7/8 | 4605 | 48 | stop |
| bytecode-vm-evolution | runtime_error | 0/6 | 18064 | 50 | stop |
| event-emitter-evolution | compile_error | 0/3 | 9537 | 50 | stop |

## Failure details

- `flat-to-tree`: runtime_error — cannot read property 'parentId' of undefined
- `paginate-and-sort`: compile_error — expecting ':'
- `deep-merge`: runtime_error — 'result' is read-only
- `csv-parse`: compile_error — continue must be inside loop
- `render-template`: runtime_error — 'key' is not defined
- `shopping-cart`: runtime_error — 'tax' is not defined
- `query-string-parser`: compile_error — expecting ':'
- `schema-validator`: failed
- `state-reducer`: runtime_error — cannot read property of undefined
- `rbac-checker`: runtime_error — cannot read property 'length' of undefined
- `i18n-pluralize`: runtime_error — not a function
- `sql-query-builder`: compile_error — invalid redefinition of lexical identifier
- `json-schema-deref-validate`: failed
- `cron-next-runs`: compile_error — extraneous characters at the end
- `longest-substring-no-repeat`: failed
- `group-anagrams`: failed
- `top-k-frequent`: runtime_error — 'k' is not defined
- `merge-intervals`: failed
- `flatten-tree`: failed
- `shortest-path-grid`: failed
- `rotate-square-matrix`: extract_error — Response did not contain export function solve(input)
- `deep-equal`: failed
- `bytecode-vm-evolution`: runtime_error — cannot read property 'startsWith' of undefined
- `event-emitter-evolution`: compile_error — expecting ';'
