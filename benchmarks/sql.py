"""SQL AST Compiler benchmark.

Tests the model's ability to implement a compiler from a query AST tree to parameterized SQL:
- Level 1: Basic SELECT, WHERE (AND, OR), ORDER BY, LIMIT, OFFSET, placeholders $1, $2...
- Level 2: JOINS (INNER, LEFT, RIGHT), GROUP BY, operators IN, IS NULL, IS NOT NULL, LIKE.
- Level 3: Expressions with aliases (COUNT(...) AS c), HAVING, subqueries (WHERE IN (SELECT...)).
"""

import re
from pathlib import Path

from benchmarks.base import Benchmark, Level, TestResult
from sandboxes import call_with_timeout, verify_function_exists

LEVEL1_PROMPT = """\
Implement a compiler from a query AST tree to parameterized SQL in a single Python file.

Input AST query dictionary:
- table (str): table name (e.g., 'users')
- select (list, optional): list of columns (list[str], defaults to ['*'])
- where (dict, optional): condition tree:
  - { field: str, op: str, value: any } — supported operators: '=', '!=', '>', '<', '>=', '<='
  - { AND: [cond1, cond2, ...] } — logical AND (if conditions > 1, wrap in parentheses (cond1 AND cond2))
  - { OR: [cond1, cond2, ...] } — logical OR (if conditions > 1, wrap in parentheses (cond1 OR cond2))
- orderBy (list[dict], optional): list of { field: str, dir?: 'ASC'|'DESC' } (defaults to dir 'ASC')
- limit (int, optional): LIMIT <limit>
- offset (int, optional): OFFSET <offset>

Parameterization rules:
- Values from where conditions are replaced with placeholders $1, $2, $3... in left-to-right traversal order.
- The actual values are collected into the params list.

Requirements:
- Single file, no external dependencies.
- Add a function compile_query(query: dict) -> dict, returning:
  {"sql": str, "params": list}
  where sql is the compiled SQL string, and params is the list of bound parameters.

Return only the code in a single ```python ... ``` block, without any explanations outside the block.
"""

LEVEL2_PROMPT = """\
Extend your SQL compiler with support for JOIN, GROUP BY, and extended operators:

1. Joins (JOINS):
   - joins: list of { type?: 'INNER'|'LEFT'|'RIGHT', table: str, on: { <left_col>: <right_col> } }
     (defaults to type 'INNER'). Example: LEFT JOIN items ON orders.id = items.order_id

2. Grouping:
   - groupBy: list of columns (list[str]). Example: GROUP BY orders.id, orders.status

3. Extended operators in where:
   - op: 'IN', value: list — generates field IN ($1, $2, ...)
   - op: 'IS NULL' — generates field IS NULL (no placeholder and not added to params)
   - op: 'IS NOT NULL' — generates field IS NOT NULL (no placeholder and not added to params)
   - op: 'LIKE', value: str — generates field LIKE $1

Do not change Level 1 behavior and preserve the compile_query(query: dict) -> dict signature.

Return only the code in a single ```python ... ``` block, without any explanations outside the block.
"""

LEVEL3_PROMPT = """\
Extend your SQL compiler with support for computed expressions in SELECT, HAVING, and subqueries:

1. Expressions with aliases in select:
   - select list element can be an object: { expr: str, as: str }
     Example: { expr: 'COUNT(items.id)', as: 'item_count' } -> SELECT orders.id, COUNT(items.id) AS item_count

2. HAVING clause:
   - having (dict, optional): condition tree in the same format as where.
     Example: HAVING SUM(sales.amount) > $1. Parameters from having continue numbering after where.

3. Subqueries in WHERE:
   - { field: str, op: 'IN', query: dict } — condition with nested query AST.
     Example: field IN (SELECT user_id FROM vip_members WHERE tier = $1)
     Subquery parameters are correctly appended to the overall params list with proper sequential placeholder numbering.

Do not change Level 1 and Level 2 behavior and preserve the compile_query(query: dict) -> dict signature.

Return only the code in a single ```python ... ``` block, without any explanations outside the block.
"""

LEVEL1_TESTS: list[tuple[str, dict, dict]] = [
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

LEVEL2_TESTS: list[tuple[str, dict, dict]] = [
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

LEVEL3_TESTS: list[tuple[str, dict, dict]] = [
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


def _norm_sql(s: str) -> str:
    """Removes extra whitespace from an SQL string."""
    return re.sub(r"\s+", " ", str(s)).strip()


def run_sql_suite(tests: list[tuple[str, dict, dict]], solution_path: str | Path) -> tuple[int, int, list[str]]:
    """Runs SQL compiler test suite and returns (passed, total, failures)."""
    passed = 0
    failures: list[str] = []

    for test_name, query, expected in tests:
        success, result = call_with_timeout(str(solution_path), "compile_query", (query,))
        if not success:
            failures.append(f"{test_name}: exception/timeout: {result}")
            continue

        if not isinstance(result, dict) or "sql" not in result or "params" not in result:
            failures.append(f"{test_name}: expected dict with 'sql' and 'params' keys, got {result}")
            continue

        res_sql = _norm_sql(result["sql"])
        exp_sql = _norm_sql(expected["sql"])
        res_params = list(result["params"])
        exp_params = list(expected["params"])

        if res_sql == exp_sql and res_params == exp_params:
            passed += 1
        else:
            diffs = []
            if res_sql != exp_sql:
                diffs.append(f"SQL: expected '{exp_sql}', got '{res_sql}'")
            if res_params != exp_params:
                diffs.append(f"params: expected {exp_params}, got {res_params}")
            failures.append(f"{test_name}: {'; '.join(diffs)}")

    return passed, len(tests), failures


class SQLBenchmark(Benchmark):
    id = "sql"
    name = "SQL AST Compiler (SELECT/WHERE/JOIN/GROUP BY/HAVING)"
    short = "SQL"
    levels = [
        Level(id="level1", name="Level 1 (SELECT/WHERE/ORDER/LIMIT)", prompt=LEVEL1_PROMPT, requires=None),
        Level(id="level2", name="Level 2 (JOIN/GROUP BY/IN/LIKE/IS NULL)", prompt=LEVEL2_PROMPT, requires="level1"),
        Level(id="level3", name="Level 3 (HAVING/Subqueries/Expr AS)", prompt=LEVEL3_PROMPT, requires="level2"),
    ]

    def run_tests(self, level_id: str, answer_path: Path) -> TestResult:
        if level_id == "level1":
            tests = LEVEL1_TESTS
        elif level_id == "level2":
            tests = LEVEL2_TESTS
        else:
            tests = LEVEL3_TESTS

        try:
            verify_function_exists(answer_path, "compile_query")
        except Exception as e:
            return TestResult(0, len(tests), [f"failed to load solution: {e}"])

        passed, total, failures = run_sql_suite(tests, answer_path)
        return TestResult(passed, total, failures)
