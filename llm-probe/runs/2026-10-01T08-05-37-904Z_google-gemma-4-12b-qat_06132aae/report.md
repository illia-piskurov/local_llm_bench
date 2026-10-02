# llm-probe benchmark report

| | |
|---|---|
| **Run** | `2026-10-01T08-05-37-904Z_google-gemma-4-12b-qat_06132aae` |
| **Status** | completed |
| **Model** | `google/gemma-4-12b-qat` |
| **Hardware** | M4 | 24GB | 10-core GPU M4 |
| **Started** | 2026-10-01T08:05:37.904Z |
| **Completed** | 2026-10-01T10:40:39.313Z |
| **Samples (k)** | 1 |
| **Tasks** | 27 |

## Accuracy

| Metric | Value |
|---|---|
| **success@1 (0-shot)** | 6/27 (22%) |

## Accuracy by category

| Category | Pass rate | Tasks |
|---|---|---|
| **product** | 0/14 (0%) | 14 |
| **strings** | 1/1 (100%) | 1 |
| **collections** | 2/2 (100%) | 2 |
| **numbers** | 0/1 (0%) | 1 |
| **structures** | 1/1 (100%) | 1 |
| **algorithms** | 1/3 (33%) | 3 |
| **correctness** | 1/3 (33%) | 3 |
| **evolution** | 0/2 (0%) | 2 |

## Latency & throughput

| | |
|---|---|
| Mean generation | 45303 ms |
| Median generation | 0 ms |
| Min / Max | 0 ms / 249713 ms |
| Mean tok/s | **10** tok/s |
| Total completion tokens | 12365 (458 tok/task) |
| **Quality/Speed Score** | **14.7** |

## Failure breakdown

| Failure type | Count |
|---|---|
| provider_error | 21 |

## Results by task

| Task | Status | Tests | Gen ms | tok/s | Finish |
|---|---|---|---|---|---|
| flat-to-tree | provider_error | 0/0 | 0 | — | — |
| paginate-and-sort | provider_error | 0/0 | 0 | — | — |
| deep-merge | provider_error | 0/0 | 0 | — | — |
| csv-parse | provider_error | 0/0 | 0 | — | — |
| render-template | provider_error | 0/0 | 0 | — | — |
| shopping-cart | provider_error | 0/0 | 0 | — | — |
| query-string-parser | provider_error | 0/0 | 0 | — | — |
| schema-validator | provider_error | 0/0 | 0 | — | — |
| state-reducer | provider_error | 0/0 | 0 | — | — |
| rbac-checker | provider_error | 0/0 | 0 | — | — |
| i18n-pluralize | provider_error | 0/0 | 0 | — | — |
| sql-query-builder | provider_error | 0/0 | 0 | — | — |
| json-schema-deref-validate | provider_error | 0/0 | 0 | — | — |
| cron-next-runs | provider_error | 0/0 | 0 | — | — |
| longest-substring-no-repeat | passed | 5/5 | 134315 | 11 | stop |
| group-anagrams | passed | 5/5 | 231996 | 11 | stop |
| top-k-frequent | passed | 5/5 | 219416 | 11 | stop |
| merge-intervals | provider_error | 0/0 | 0 | — | — |
| flatten-tree | passed | 4/4 | 242711 | 10 | stop |
| shortest-path-grid | provider_error | 0/0 | 0 | — | — |
| lcs-length | provider_error | 0/0 | 0 | — | — |
| topological-sort | passed | 5/5 | 249713 | 9 | stop |
| rotate-square-matrix | provider_error | 0/0 | 0 | — | — |
| validate-sudoku-board | passed | 4/4 | 145034 | 9 | stop |
| deep-equal | provider_error | 0/0 | 0 | — | — |
| bytecode-vm-evolution | provider_error | 0/0 | 0 | — | — |
| event-emitter-evolution | provider_error | 0/0 | 0 | — | — |

## Failure details

- `flat-to-tree`: provider_error — Cannot connect to http://127.0.0.1:1234/v1: fetch failed
- `paginate-and-sort`: provider_error — Cannot connect to http://127.0.0.1:1234/v1: fetch failed
- `deep-merge`: provider_error — Provider returned HTTP 400
- `csv-parse`: provider_error — Cannot connect to http://127.0.0.1:1234/v1: fetch failed
- `render-template`: provider_error — Cannot connect to http://127.0.0.1:1234/v1: fetch failed
- `shopping-cart`: provider_error — Cannot connect to http://127.0.0.1:1234/v1: fetch failed
- `query-string-parser`: provider_error — Cannot connect to http://127.0.0.1:1234/v1: fetch failed
- `schema-validator`: provider_error — Cannot connect to http://127.0.0.1:1234/v1: fetch failed
- `state-reducer`: provider_error — Cannot connect to http://127.0.0.1:1234/v1: fetch failed
- `rbac-checker`: provider_error — Cannot connect to http://127.0.0.1:1234/v1: fetch failed
- `i18n-pluralize`: provider_error — Cannot connect to http://127.0.0.1:1234/v1: fetch failed
- `sql-query-builder`: provider_error — Cannot connect to http://127.0.0.1:1234/v1: fetch failed
- `json-schema-deref-validate`: provider_error — Cannot connect to http://127.0.0.1:1234/v1: fetch failed
- `cron-next-runs`: provider_error — Cannot connect to http://127.0.0.1:1234/v1: fetch failed
- `merge-intervals`: provider_error — Cannot connect to http://127.0.0.1:1234/v1: fetch failed
- `shortest-path-grid`: provider_error — Cannot connect to http://127.0.0.1:1234/v1: fetch failed
- `lcs-length`: provider_error — Cannot connect to http://127.0.0.1:1234/v1: fetch failed
- `rotate-square-matrix`: provider_error — Cannot connect to http://127.0.0.1:1234/v1: fetch failed
- `deep-equal`: provider_error — Cannot connect to http://127.0.0.1:1234/v1: fetch failed
- `bytecode-vm-evolution`: provider_error — Cannot connect to http://127.0.0.1:1234/v1: fetch failed
- `event-emitter-evolution`: provider_error — Cannot connect to http://127.0.0.1:1234/v1: fetch failed
