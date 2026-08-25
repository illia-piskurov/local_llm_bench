# llm-probe benchmark report

| | |
|---|---|
| **Run** | `2026-08-18T07-13-20-203Z_mistralai-ministral-3-3b_0e7ecc98` |
| **Status** | completed |
| **Model** | `mistralai/ministral-3-3b` |
| **Started** | 2026-08-18T07:13:20.203Z |
| **Completed** | 2026-08-18T07:15:31.165Z |
| **Samples (k)** | 1 |
| **Tasks** | 17 |

## Accuracy

| Metric | Value |
|---|---|
| **success@1** | 11/17 (65%) |

## Latency & throughput

| | |
|---|---|
| Mean generation | 7613 ms |
| Median generation | 6343 ms |
| Min / Max | 2793 ms / 16725 ms |
| Mean tok/s | **19** tok/s |
| Total completion tokens | 2416 |

## Failure breakdown

| Failure type | Count |
|---|---|
| failed | 6 |

## Results by task

| Task | Status | Tests | Gen ms | tok/s | Finish |
|---|---|---|---|---|---|
| first-unique-char | passed | 6/6 | 4250 | 23 | stop |
| run-length-encode | failed | 4/5 | 5478 | 21 | stop |
| longest-substring-no-repeat | passed | 5/5 | 6032 | 19 | stop |
| group-anagrams | failed | 4/5 | 5936 | 19 | stop |
| top-k-frequent | passed | 5/5 | 6343 | 18 | stop |
| frequency-map | passed | 4/4 | 3672 | 17 | stop |
| merge-intervals | failed | 0/6 | 6749 | 19 | stop |
| count-primes | passed | 6/6 | 6346 | 20 | stop |
| balanced-brackets | passed | 6/6 | 6416 | 19 | stop |
| flatten-tree | passed | 4/4 | 5071 | 17 | stop |
| two-sum-indices | passed | 5/5 | 5687 | 18 | stop |
| shortest-path-grid | failed | 1/4 | 14589 | 19 | stop |
| lcs-length | passed | 5/5 | 9574 | 19 | stop |
| topological-sort | passed | 5/5 | 10969 | 18 | stop |
| rotate-square-matrix | failed | 2/4 | 2793 | 13 | stop |
| validate-sudoku-board | failed | 3/4 | 16725 | 18 | stop |
| deep-equal | passed | 8/8 | 12788 | 19 | stop |

## Failure details

- `run-length-encode`: failed
- `group-anagrams`: failed
- `merge-intervals`: failed
- `shortest-path-grid`: failed
- `rotate-square-matrix`: failed
- `validate-sudoku-board`: failed
