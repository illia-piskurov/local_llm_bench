# llm-probe benchmark report

| | |
|---|---|
| **Run** | `2026-08-18T16-59-33-659Z_google-gemma-4-e4b_3787448c` |
| **Status** | completed |
| **Model** | `google/gemma-4-e4b` |
| **Hardware** | AMD RYZEN 7 250 | 32 GB 5600 | 780m Radeon |
| **Started** | 2026-08-18T16:59:33.659Z |
| **Completed** | 2026-08-18T17:41:31.128Z |
| **Samples (k)** | 1 |
| **Tasks** | 27 |

## Accuracy

| Metric | Value |
|---|---|
| **success@1 (0-shot)** | 13/27 (48%) |

## Accuracy by category

| Category | Pass rate | Tasks |
|---|---|---|
| **product** | 2/14 (14%) | 14 |
| **strings** | 1/1 (100%) | 1 |
| **collections** | 2/2 (100%) | 2 |
| **numbers** | 1/1 (100%) | 1 |
| **structures** | 1/1 (100%) | 1 |
| **algorithms** | 3/3 (100%) | 3 |
| **correctness** | 3/3 (100%) | 3 |
| **evolution** | 0/2 (0%) | 2 |

## Latency & throughput

| | |
|---|---|
| Mean generation | 30961 ms |
| Median generation | 0 ms |
| Min / Max | 0 ms / 114117 ms |
| Mean tok/s | **14** tok/s |
| Total completion tokens | 11934 (442 tok/task) |
| **Quality/Speed Score** | **38.9** |

## Failure breakdown

| Failure type | Count |
|---|---|
| provider_error | 14 |

## Results by task

| Task | Status | Tests | Gen ms | tok/s | Finish |
|---|---|---|---|---|---|
| flat-to-tree | provider_error | 0/0 | 0 | — | — |
| paginate-and-sort | provider_error | 0/0 | 0 | — | — |
| deep-merge | provider_error | 0/0 | 0 | — | — |
| csv-parse | provider_error | 0/0 | 0 | — | — |
| render-template | provider_error | 0/0 | 0 | — | — |
| shopping-cart | passed | 4/4 | 84277 | 13 | stop |
| query-string-parser | provider_error | 0/0 | 0 | — | — |
| schema-validator | provider_error | 0/0 | 0 | — | — |
| state-reducer | provider_error | 0/0 | 0 | — | — |
| rbac-checker | passed | 3/3 | 101945 | 13 | stop |
| i18n-pluralize | provider_error | 0/0 | 0 | — | — |
| sql-query-builder | provider_error | 0/0 | 0 | — | — |
| json-schema-deref-validate | provider_error | 0/0 | 0 | — | — |
| cron-next-runs | provider_error | 0/0 | 0 | — | — |
| longest-substring-no-repeat | passed | 5/5 | 14495 | 14 | stop |
| group-anagrams | passed | 5/5 | 114117 | 15 | stop |
| top-k-frequent | passed | 5/5 | 24600 | 14 | stop |
| merge-intervals | passed | 6/6 | 110820 | 14 | stop |
| flatten-tree | passed | 4/4 | 62422 | 14 | stop |
| shortest-path-grid | passed | 4/4 | 95714 | 14 | stop |
| lcs-length | passed | 5/5 | 19292 | 19 | stop |
| topological-sort | passed | 5/5 | 97644 | 18 | stop |
| rotate-square-matrix | passed | 4/4 | 20915 | 15 | stop |
| validate-sudoku-board | passed | 4/4 | 32522 | 13 | stop |
| deep-equal | passed | 8/8 | 57186 | 12 | stop |
| bytecode-vm-evolution | provider_error | 0/0 | 0 | — | — |
| event-emitter-evolution | provider_error | 0/0 | 0 | — | — |

## Failure details

- `flat-to-tree`: provider_error — Request to http://127.0.0.1:1234/v1 timed out after 120000ms
- `paginate-and-sort`: provider_error — Request to http://127.0.0.1:1234/v1 timed out after 120000ms
- `deep-merge`: provider_error — Request to http://127.0.0.1:1234/v1 timed out after 120000ms
- `csv-parse`: provider_error — Request to http://127.0.0.1:1234/v1 timed out after 120000ms
- `render-template`: provider_error — Request to http://127.0.0.1:1234/v1 timed out after 120000ms
- `query-string-parser`: provider_error — Request to http://127.0.0.1:1234/v1 timed out after 120000ms
- `schema-validator`: provider_error — Request to http://127.0.0.1:1234/v1 timed out after 120000ms
- `state-reducer`: provider_error — Request to http://127.0.0.1:1234/v1 timed out after 120000ms
- `i18n-pluralize`: provider_error — Request to http://127.0.0.1:1234/v1 timed out after 120000ms
- `sql-query-builder`: provider_error — Request to http://127.0.0.1:1234/v1 timed out after 120000ms
- `json-schema-deref-validate`: provider_error — Request to http://127.0.0.1:1234/v1 timed out after 120000ms
- `cron-next-runs`: provider_error — Request to http://127.0.0.1:1234/v1 timed out after 120000ms
- `bytecode-vm-evolution`: provider_error — Request to http://127.0.0.1:1234/v1 timed out after 120000ms
- `event-emitter-evolution`: provider_error — Request to http://127.0.0.1:1234/v1 timed out after 120000ms
