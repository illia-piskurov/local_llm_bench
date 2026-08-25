# llm-probe benchmark report

| | |
|---|---|
| **Run** | `2026-08-18T07-54-05-484Z_mistralai-ministral-3-3b_8d33a08c` |
| **Status** | completed |
| **Model** | `mistralai/ministral-3-3b` |
| **Hardware** | AMD RYZEN 7 250 | 32 GB 5600 | 780m Radeon |
| **Started** | 2026-08-18T07:54:05.484Z |
| **Completed** | 2026-08-18T07:54:26.406Z |
| **Samples (k)** | 1 |
| **Tasks** | 1 |

## Accuracy

| Metric | Value |
|---|---|
| **success@1** | 0/1 (0%) |

## Latency & throughput

| | |
|---|---|
| Mean generation | 20832 ms |
| Median generation | 20832 ms |
| Min / Max | 20832 ms / 20832 ms |
| Mean tok/s | **20** tok/s |
| Total completion tokens | 420 |

## Failure breakdown

| Failure type | Count |
|---|---|
| failed | 1 |

## Results by task

| Task | Status | Tests | Gen ms | tok/s | Finish |
|---|---|---|---|---|---|
| shopping-cart | failed | 0/4 | 20832 | 20 | stop |

## Failure details

- `shopping-cart`: failed
