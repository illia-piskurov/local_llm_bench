# llm-probe benchmark report

| | |
|---|---|
| **Run** | `2026-08-18T07-42-55-578Z_mistralai-ministral-3-3b_cc8065da` |
| **Status** | completed |
| **Model** | `mistralai/ministral-3-3b` |
| **Started** | 2026-08-18T07:42:55.578Z |
| **Completed** | 2026-08-18T07:43:28.491Z |
| **Samples (k)** | 1 |
| **Tasks** | 1 |

## Accuracy

| Metric | Value |
|---|---|
| **success@1** | 0/1 (0%) |

## Latency & throughput

| | |
|---|---|
| Mean generation | 32817 ms |
| Median generation | 32817 ms |
| Min / Max | 32817 ms / 32817 ms |
| Mean tok/s | **20** tok/s |
| Total completion tokens | 658 |

## Failure breakdown

| Failure type | Count |
|---|---|
| failed | 1 |

## Results by task

| Task | Status | Tests | Gen ms | tok/s | Finish |
|---|---|---|---|---|---|
| query-string-parser | failed | 2/5 | 32817 | 20 | stop |

## Failure details

- `query-string-parser`: failed
