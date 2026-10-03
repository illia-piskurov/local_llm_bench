"""In-memory Key-Value store with transactions benchmark.

Tests the model's ability to implement an in-memory database:
- Level 1: SET, GET, DELETE, nested transactions (BEGIN, COMMIT, ROLLBACK).
- Level 2: Aggregations (COUNT) and reactive listeners (WATCH key).
- Level 3: Full state snapshots and restoration (SNAPSHOT / RESTORE).
"""

from pathlib import Path
from typing import Any

from benchmarks.base import Benchmark, Level, TestResult
from sandboxes import call_with_timeout, verify_function_exists

LEVEL1_PROMPT = """\
Implement an in-memory key-value store with nested transactions in a single Python file.

Supported commands (one per line, arguments separated by space):
SET <key> <value>  — set the value of a key
GET <key>          — output the current value of the key, or "NULL" if the key is not set
DELETE <key>       — delete the key (if key does not exist — do nothing, no error)
BEGIN              — start a new (potentially nested) transaction
COMMIT             — commit the innermost open transaction, merging its changes
                     into the parent transaction (not directly into global storage if
                     it is a nested transaction). If there are no open transactions — output
                     "NO TRANSACTION"
ROLLBACK           — rollback the innermost open transaction, discarding all changes
                     made within it. If there are no open transactions — output
                     "NO TRANSACTION"

Ignore empty lines.

Requirements:
- Single file, no external dependencies.
- Transactions can be nested arbitrarily deep.
- Changes made within a transaction must be visible via GET immediately (even before COMMIT),
  but must be completely discarded on ROLLBACK.
- Add a function run(program: str) -> list[str], returning a list of output strings —
  one string for each GET command, as well as for COMMIT/ROLLBACK when they output
  "NO TRANSACTION" (other commands produce no output).

Return only the code in a single ```python ... ``` block, without any explanations outside the block.
"""

LEVEL2_PROMPT = """\
Extend your implementation with two new commands:

COUNT <value>  — output the number of keys whose current value (taking into account open
                transactions) is equal to <value>
WATCH <key>    — start watching a key. From this moment on, any SET or DELETE
                that modifies the currently visible value of this key (including
                changes inside uncommitted transactions) must immediately output:
                "WATCH <key> <old_value> -> <new_value>"
                where "NULL" is used in place of an absent value.
                If SET assigns the same value that already exists — no notification is emitted.
                WATCH notifications are emitted immediately at the moment of SET/DELETE execution,
                not at COMMIT/ROLLBACK.

Do not change the behavior of previously implemented commands and preserve the run(program: str) -> list[str] signature.

Return only the code in a single ```python ... ``` block, without any explanations outside the block.
"""

LEVEL3_PROMPT = """\
Extend your implementation with snapshot/restore commands:

SNAPSHOT <name>  — save the complete current state of the store under name <name>.
                   Everything is preserved: global values, all open transactions,
                   watched keys, and any internal structures needed
                   for run() to function correctly.
RESTORE <name>   — restore the complete state from a previously saved snapshot.
                   After RESTORE, the store must behave as if the program
                   continued execution from the moment of SNAPSHOT. RESTORE does not print
                   anything and by itself must not trigger WATCH notifications.

Requirements:
- SNAPSHOT can be called inside nested transactions, and RESTORE must restore
  the exact state that was saved, including the depth of the transaction stack.
- If a snapshot with this name already exists, overwrite it.
- RESTORE to an unknown snapshot can be considered an error or unexpected situation,
  but this case is not tested.
- Do not change the behavior of previously implemented commands and preserve the run(program: str) -> list[str] signature.

Return only the code in a single ```python ... ``` block, without any explanations outside the block.
"""

LEVEL1_TESTS: list[tuple[str, str, list[str]]] = [
    ("basic_set_get", "SET a 10\nGET a", ["10"]),
    ("get_missing", "GET x", ["NULL"]),
    ("delete_then_get", "SET a 10\nDELETE a\nGET a", ["NULL"]),
    ("delete_missing_key_noop", "DELETE x\nGET x", ["NULL"]),
    ("overwrite_set", "SET a 1\nSET a 2\nGET a", ["2"]),
    ("commit_no_transaction", "COMMIT", ["NO TRANSACTION"]),
    ("rollback_no_transaction", "ROLLBACK", ["NO TRANSACTION"]),
    ("simple_transaction_commit", "BEGIN\nSET a 10\nCOMMIT\nGET a", ["10"]),
    ("simple_transaction_rollback", "SET a 5\nBEGIN\nSET a 10\nROLLBACK\nGET a", ["5"]),
    ("rollback_restores_delete", "SET a 5\nBEGIN\nDELETE a\nGET a\nROLLBACK\nGET a", ["NULL", "5"]),
    (
        "nested_transactions",
        "BEGIN\nSET a 10\nBEGIN\nSET a 20\nGET a\nROLLBACK\nGET a\nROLLBACK\nGET a",
        ["20", "10", "NULL"],
    ),
    (
        "nested_commit_propagates_to_outer_only",
        "BEGIN\nSET a 1\nBEGIN\nSET a 2\nCOMMIT\nGET a\nCOMMIT\nGET a",
        ["2", "2"],
    ),
    ("rollback_after_commit_is_no_transaction", "BEGIN\nSET a 1\nCOMMIT\nROLLBACK", ["NO TRANSACTION"]),
    ("multiple_keys_independent", "SET a 1\nSET b 2\nBEGIN\nSET a 99\nGET b\nROLLBACK\nGET a\nGET b", ["2", "1", "2"]),
    ("set_new_key_inside_transaction", "BEGIN\nSET x 100\nGET x\nCOMMIT\nGET x", ["100", "100"]),
]

LEVEL2_TESTS: list[tuple[str, str, list[str]]] = [
    ("count_basic", "SET a 1\nSET b 1\nSET c 2\nCOUNT 1", ["2"]),
    ("count_zero", "COUNT 5", ["0"]),
    ("count_respects_transaction", "SET a 1\nBEGIN\nSET b 1\nCOUNT 1\nROLLBACK\nCOUNT 1", ["2", "1"]),
    ("count_after_delete", "SET a 1\nSET b 1\nDELETE a\nCOUNT 1", ["1"]),
    ("watch_set_new_key", "WATCH a\nSET a 10", ["WATCH a NULL -> 10"]),
    ("watch_set_change", "SET a 5\nWATCH a\nSET a 10", ["WATCH a 5 -> 10"]),
    ("watch_no_change_no_notification", "SET a 5\nWATCH a\nSET a 5", []),
    ("watch_delete", "SET a 5\nWATCH a\nDELETE a", ["WATCH a 5 -> NULL"]),
    ("watch_unrelated_key_silent", "WATCH a\nSET b 1", []),
    ("watch_inside_transaction_fires", "WATCH a\nBEGIN\nSET a 1", ["WATCH a NULL -> 1"]),
]

LEVEL3_TESTS: list[tuple[str, str, list[str]]] = [
    (
        "snapshot_restores_full_state",
        "SET a 1\nBEGIN\nSET a 2\nSNAPSHOT s\nSET a 3\nRESTORE s\nGET a\nCOMMIT\nGET a",
        ["2", "2"],
    ),
    (
        "snapshot_is_deep_copied",
        "SET a 1\nSNAPSHOT s1\nSET a 2\nSNAPSHOT s2\nSET a 3\nRESTORE s1\nGET a\nRESTORE s2\nGET a",
        ["1", "2"],
    ),
    (
        "restore_preserves_open_transactions",
        "BEGIN\nSET a 1\nSNAPSHOT s\nSET a 2\nROLLBACK\nRESTORE s\nCOMMIT\nGET a",
        ["1"],
    ),
    (
        "restore_keeps_watch_registrations",
        "WATCH a\nSET a 1\nSNAPSHOT s\nSET a 2\nRESTORE s\nSET a 3",
        ["WATCH a NULL -> 1", "WATCH a 1 -> 2", "WATCH a 1 -> 3"],
    ),
    (
        "snapshot_inside_nested_transactions",
        "BEGIN\nSET a 1\nBEGIN\nSET b 2\nSNAPSHOT s\nSET a 3\nROLLBACK\nRESTORE s\nGET a\nGET b\nCOMMIT\nGET a\nGET b",
        ["1", "2", "1", "2"],
    ),
]


def _norm(values: Any) -> list[str]:
    if not isinstance(values, (list, tuple)):
        return [str(values)]
    return [str(v) for v in values]


def run_kv_suite(tests: list[tuple[str, str, list[str]]], solution_path: str | Path) -> tuple[int, int, list[str]]:
    passed = 0
    failures: list[str] = []

    for test_name, program, expected in tests:
        success, result = call_with_timeout(str(solution_path), "run", (program,))
        if not success:
            failures.append(f"{test_name}: unexpected exception/timeout: {result}")
            continue

        result_norm = _norm(result)
        if result_norm == expected:
            passed += 1
        else:
            failures.append(f"{test_name}: expected {expected}, got {result_norm}")

    return passed, len(tests), failures


class KVBenchmark(Benchmark):
    id = "kv"
    name = "Transactional KV Store (SET/GET/BEGIN/COMMIT/ROLLBACK/SNAPSHOT)"
    short = "KV"
    levels = [
        Level(id="level1", name="Level 1 (SET/GET/DELETE + transactions)", prompt=LEVEL1_PROMPT, requires=None),
        Level(id="level2", name="Level 2 (COUNT/WATCH)", prompt=LEVEL2_PROMPT, requires="level1"),
        Level(id="level3", name="Level 3 (SNAPSHOT/RESTORE)", prompt=LEVEL3_PROMPT, requires="level2"),
    ]

    def run_tests(self, level_id: str, answer_path: Path) -> TestResult:
        if level_id == "level1":
            tests = LEVEL1_TESTS
        elif level_id == "level2":
            tests = LEVEL1_TESTS + LEVEL2_TESTS
        else:
            tests = LEVEL1_TESTS + LEVEL2_TESTS + LEVEL3_TESTS

        try:
            verify_function_exists(answer_path, "run")
        except Exception as e:
            return TestResult(0, len(tests), [f"failed to load solution: {e}"])

        passed, total, failures = run_kv_suite(tests, answer_path)
        return TestResult(passed, total, failures)
