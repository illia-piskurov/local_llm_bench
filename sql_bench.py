"""
Бенчмарк для локальных LLM: компилятор AST-дерева запроса в параметризованный SQL.

Использование:
    python sql_bench.py path/to/solution.py

Файл solution.py должен содержать функцию:
    compile_query(query: dict) -> dict
где:
    query: словарь AST запроса
возвращает:
    {"sql": str, "params": list}
"""

import importlib.util
import re
import sys
import traceback

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from timeout_utils import call_with_timeout


def load_compile_query(path: str):
    spec = importlib.util.spec_from_file_location("solution", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if not hasattr(module, "compile_query"):
        raise AttributeError("В решении не найдена функция compile_query(query: dict) -> dict")
    return module.compile_query


LEVEL1_TESTS = [
    (
        "simple_select_all",
        {"table": "products"},
        {"sql": "SELECT * FROM products", "params": []},
    ),
    (
        "select_specific_columns",
        {"table": "users", "select": ["id", "email", "created_at"]},
        {"sql": "SELECT id, email, created_at FROM users", "params": []},
    ),
    (
        "simple_where_equality",
        {"table": "users", "where": {"field": "status", "op": "=", "value": "active"}},
        {"sql": "SELECT * FROM users WHERE status = $1", "params": ["active"]},
    ),
    (
        "where_and_or_nested",
        {
            "table": "users",
            "select": ["id", "email"],
            "where": {
                "AND": [
                    {"field": "status", "op": "=", "value": "active"},
                    {
                        "OR": [
                            {"field": "role", "op": "=", "value": "admin"},
                            {"field": "age", "op": ">=", "value": 21},
                        ]
                    },
                ]
            },
        },
        {
            "sql": "SELECT id, email FROM users WHERE (status = $1 AND (role = $2 OR age >= $3))",
            "params": ["active", "admin", 21],
        },
    ),
    (
        "order_by_limit_offset",
        {
            "table": "articles",
            "orderBy": [{"field": "views", "dir": "DESC"}, {"field": "id", "dir": "ASC"}],
            "limit": 10,
            "offset": 20,
        },
        {"sql": "SELECT * FROM articles ORDER BY views DESC, id ASC LIMIT 10 OFFSET 20", "params": []},
    ),
    (
        "multiple_and_conditions",
        {
            "table": "logs",
            "where": {
                "AND": [
                    {"field": "level", "op": "=", "value": "error"},
                    {"field": "code", "op": "!=", "value": 404},
                    {"field": "timestamp", "op": ">", "value": 1000},
                ]
            },
        },
        {
            "sql": "SELECT * FROM logs WHERE (level = $1 AND code != $2 AND timestamp > $3)",
            "params": ["error", 404, 1000],
        },
    ),
]

LEVEL2_TESTS = [
    (
        "left_join_with_group_by",
        {
            "table": "orders",
            "select": ["orders.id", "orders.total"],
            "joins": [{"type": "LEFT", "table": "items", "on": {"orders.id": "items.order_id"}}],
            "groupBy": ["orders.id", "orders.total"],
        },
        {
            "sql": "SELECT orders.id, orders.total FROM orders LEFT JOIN items ON orders.id = items.order_id GROUP BY orders.id, orders.total",
            "params": [],
        },
    ),
    (
        "multiple_joins_inner_and_left",
        {
            "table": "posts",
            "select": ["posts.title", "users.name"],
            "joins": [
                {"type": "INNER", "table": "users", "on": {"posts.author_id": "users.id"}},
                {"type": "LEFT", "table": "comments", "on": {"posts.id": "comments.post_id"}},
            ],
        },
        {
            "sql": "SELECT posts.title, users.name FROM posts INNER JOIN users ON posts.author_id = users.id LEFT JOIN comments ON posts.id = comments.post_id",
            "params": [],
        },
    ),
    (
        "where_in_operator",
        {"table": "users", "where": {"field": "id", "op": "IN", "value": [10, 20, 30]}},
        {"sql": "SELECT * FROM users WHERE id IN ($1, $2, $3)", "params": [10, 20, 30]},
    ),
    (
        "where_is_null_and_like",
        {
            "table": "customers",
            "where": {
                "AND": [
                    {"field": "deleted_at", "op": "IS NULL"},
                    {"field": "email", "op": "LIKE", "value": "%@example.com"},
                ]
            },
        },
        {"sql": "SELECT * FROM customers WHERE (deleted_at IS NULL AND email LIKE $1)", "params": ["%@example.com"]},
    ),
    (
        "where_is_not_null",
        {"table": "tasks", "where": {"field": "completed_at", "op": "IS NOT NULL"}},
        {"sql": "SELECT * FROM tasks WHERE completed_at IS NOT NULL", "params": []},
    ),
]

LEVEL3_TESTS = [
    (
        "select_expression_alias",
        {
            "table": "orders",
            "select": ["orders.id", {"expr": "COUNT(items.id)", "as": "item_count"}],
            "joins": [{"type": "LEFT", "table": "items", "on": {"orders.id": "items.order_id"}}],
            "groupBy": ["orders.id"],
        },
        {
            "sql": "SELECT orders.id, COUNT(items.id) AS item_count FROM orders LEFT JOIN items ON orders.id = items.order_id GROUP BY orders.id",
            "params": [],
        },
    ),
    (
        "having_clause",
        {
            "table": "sales",
            "select": ["sales.category", {"expr": "SUM(sales.amount)", "as": "total_sales"}],
            "groupBy": ["sales.category"],
            "having": {"field": "SUM(sales.amount)", "op": ">", "value": 1000},
        },
        {
            "sql": "SELECT sales.category, SUM(sales.amount) AS total_sales FROM sales GROUP BY sales.category HAVING SUM(sales.amount) > $1",
            "params": [1000],
        },
    ),
    (
        "where_subquery_in",
        {
            "table": "users",
            "select": ["id", "name"],
            "where": {
                "field": "id",
                "op": "IN",
                "query": {
                    "table": "vip_members",
                    "select": ["user_id"],
                    "where": {"field": "tier", "op": "=", "value": "gold"},
                },
            },
        },
        {
            "sql": "SELECT id, name FROM users WHERE id IN (SELECT user_id FROM vip_members WHERE tier = $1)",
            "params": ["gold"],
        },
    ),
    (
        "subquery_with_parent_params_order",
        {
            "table": "posts",
            "where": {
                "AND": [
                    {"field": "status", "op": "=", "value": "published"},
                    {
                        "field": "author_id",
                        "op": "IN",
                        "query": {
                            "table": "banned_authors",
                            "select": ["id"],
                            "where": {"field": "reason", "op": "=", "value": "spam"},
                        },
                    },
                    {"field": "views", "op": ">", "value": 500},
                ]
            },
        },
        {
            "sql": "SELECT * FROM posts WHERE (status = $1 AND author_id IN (SELECT id FROM banned_authors WHERE reason = $2) AND views > $3)",
            "params": ["published", "spam", 500],
        },
    ),
]


def norm_sql(s: str) -> str:
    """Убирает лишние пробелы из SQL строки."""
    return re.sub(r"\s+", " ", str(s)).strip()


def run_suite(name: str, tests: list, path: str):
    passed = 0
    failed = []
    for test_name, query, expected in tests:
        success, result = call_with_timeout(path, "compile_query", (query,))
        if not success:
            failed.append((test_name, f"исключение/таймаут: {result}"))
            continue

        if not isinstance(result, dict) or "sql" not in result or "params" not in result:
            failed.append((test_name, f"ожидался dict с ключами 'sql' и 'params', получено {result}"))
            continue

        res_sql = norm_sql(result["sql"])
        exp_sql = norm_sql(expected["sql"])
        res_params = list(result["params"])
        exp_params = list(expected["params"])

        if res_sql == exp_sql and res_params == exp_params:
            passed += 1
        else:
            diffs = []
            if res_sql != exp_sql:
                diffs.append(f"SQL: ожидали '{exp_sql}', получили '{res_sql}'")
            if res_params != exp_params:
                diffs.append(f"params: ожидали {exp_params}, получили {res_params}")
            failed.append((test_name, "; ".join(diffs)))

    total = len(tests)
    print(f"\n=== {name}: {passed}/{total} ===")
    for test_name, reason in failed:
        print(f"  [FAIL] {test_name}: {reason}")
    failures = [f"{test_name}: {reason}" for test_name, reason in failed]
    return passed, total, failures


def main():
    if len(sys.argv) != 2:
        print("Использование: python sql_bench.py path/to/solution.py")
        sys.exit(1)

    path = sys.argv[1]
    try:
        load_compile_query(path)
    except Exception as e:
        print(f"Не удалось загрузить решение: {e}")
        traceback.print_exc()
        sys.exit(1)

    p1, t1, _ = run_suite("LEVEL 1", LEVEL1_TESTS, path)
    p2, t2, _ = run_suite("LEVEL 2", LEVEL2_TESTS, path)
    p3, t3, _ = run_suite("LEVEL 3", LEVEL3_TESTS, path)

    print("\n=== ИТОГО ===")
    print(f"Level 1: {p1}/{t1}")
    print(f"Level 2: {p2}/{t2}")
    print(f"Level 3: {p3}/{t3}")
    print(f"Всего:   {p1 + p2 + p3}/{t1 + t2 + t3}")


if __name__ == "__main__":
    main()
