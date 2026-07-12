"""
Тесты для бенчмарка "in-memory key-value store с транзакциями".

Решение должно предоставлять run(program: str) -> list[str], как и VM-бенчмарк —
поэтому тестовый раннер здесь не нужен, используется bench.load_run / bench.run_suite.
"""

# Каждый тест: (имя, программа, ожидаемый список строк вывода)

LEVEL1_TESTS = [
    (
        "basic_set_get",
        "SET a 10\nGET a",
        ["10"],
    ),
    (
        "get_missing",
        "GET x",
        ["NULL"],
    ),
    (
        "delete_then_get",
        "SET a 10\nDELETE a\nGET a",
        ["NULL"],
    ),
    (
        "delete_missing_key_noop",
        "DELETE x\nGET x",
        ["NULL"],
    ),
    (
        "overwrite_set",
        "SET a 1\nSET a 2\nGET a",
        ["2"],
    ),
    (
        "commit_no_transaction",
        "COMMIT",
        ["NO TRANSACTION"],
    ),
    (
        "rollback_no_transaction",
        "ROLLBACK",
        ["NO TRANSACTION"],
    ),
    (
        "simple_transaction_commit",
        "BEGIN\nSET a 10\nCOMMIT\nGET a",
        ["10"],
    ),
    (
        "simple_transaction_rollback",
        "SET a 5\nBEGIN\nSET a 10\nROLLBACK\nGET a",
        ["5"],
    ),
    (
        "rollback_restores_delete",
        "SET a 5\nBEGIN\nDELETE a\nGET a\nROLLBACK\nGET a",
        ["NULL", "5"],
    ),
    (
        "nested_transactions",
        "BEGIN\nSET a 10\nBEGIN\nSET a 20\nGET a\nROLLBACK\nGET a\nROLLBACK\nGET a",
        ["20", "10", "NULL"],
    ),
    (
        "nested_commit_propagates_to_outer_only",
        # внутренний COMMIT должен слить изменения в родительскую транзакцию,
        # а не сразу в глобальное хранилище
        "BEGIN\nSET a 1\nBEGIN\nSET a 2\nCOMMIT\nGET a\nCOMMIT\nGET a",
        ["2", "2"],
    ),
    (
        "rollback_after_commit_is_no_transaction",
        "BEGIN\nSET a 1\nCOMMIT\nROLLBACK",
        ["NO TRANSACTION"],
    ),
    (
        "multiple_keys_independent",
        "SET a 1\nSET b 2\nBEGIN\nSET a 99\nGET b\nROLLBACK\nGET a\nGET b",
        ["2", "1", "2"],
    ),
    (
        "set_new_key_inside_transaction",
        "BEGIN\nSET x 100\nGET x\nCOMMIT\nGET x",
        ["100", "100"],
    ),
]

LEVEL2_TESTS = [
    (
        "count_basic",
        "SET a 1\nSET b 1\nSET c 2\nCOUNT 1",
        ["2"],
    ),
    (
        "count_zero",
        "COUNT 5",
        ["0"],
    ),
    (
        "count_respects_transaction",
        "SET a 1\nBEGIN\nSET b 1\nCOUNT 1\nROLLBACK\nCOUNT 1",
        ["2", "1"],
    ),
    (
        "count_after_delete",
        "SET a 1\nSET b 1\nDELETE a\nCOUNT 1",
        ["1"],
    ),
    (
        "watch_set_new_key",
        "WATCH a\nSET a 10",
        ["WATCH a NULL -> 10"],
    ),
    (
        "watch_set_change",
        "SET a 5\nWATCH a\nSET a 10",
        ["WATCH a 5 -> 10"],
    ),
    (
        "watch_no_change_no_notification",
        "SET a 5\nWATCH a\nSET a 5",
        [],
    ),
    (
        "watch_delete",
        "SET a 5\nWATCH a\nDELETE a",
        ["WATCH a 5 -> NULL"],
    ),
    (
        "watch_unrelated_key_silent",
        "WATCH a\nSET b 1",
        [],
    ),
    (
        "watch_inside_transaction_fires",
        "WATCH a\nBEGIN\nSET a 1",
        ["WATCH a NULL -> 1"],
    ),
]

LEVEL3_TESTS = [
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
