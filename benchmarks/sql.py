"""SQL AST Compiler бенчмарк.

Тестирует способность модели реализовать компилятор AST-дерева запроса в параметризованный SQL:
- Level 1: Базовый SELECT, WHERE (AND, OR), ORDER BY, LIMIT, OFFSET, плейсхолдеры $1, $2...
- Level 2: JOINS (INNER, LEFT, RIGHT), GROUP BY, операторы IN, IS NULL, IS NOT NULL, LIKE.
- Level 3: Выражения с алиасами (COUNT(...) AS c), HAVING, вложенные подзапросы (WHERE IN (SELECT...)).
"""

import re
from pathlib import Path

from benchmarks.base import Benchmark, Level, TestResult
from sandboxes import call_with_timeout, verify_function_exists

LEVEL1_PROMPT = """\
Реализуй компилятор AST-дерева запроса в параметризованный SQL в одном Python файле.

Входной словарь AST запроса:
- table (str): имя таблицы (например, 'users')
- select (list, опционально): список колонок (list[str], по умолчанию ['*'])
- where (dict, опционально): дерево условий:
  - { field: str, op: str, value: any } — поддерживаемые операторы: '=', '!=', '>', '<', '>=', '<='
  - { AND: [cond1, cond2, ...] } — логическое И (если условий > 1, оборачивается в скобки (cond1 AND cond2))
  - { OR: [cond1, cond2, ...] } — логическое ИЛИ (если условий > 1, оборачивается в скобки (cond1 OR cond2))
- orderBy (list[dict], опционально): список { field: str, dir?: 'ASC'|'DESC' } (по умолчанию dir 'ASC')
- limit (int, опционально): LIMIT <limit>
- offset (int, опционально): OFFSET <offset>

Правила параметризации:
- Значения из условий where заменяются на плейсхолдеры $1, $2, $3... в порядке их обхода слева направо.
- Сами значения собираются в список params.

Требования:
- Один файл, без внешних зависимостей.
- Добавь функцию compile_query(query: dict) -> dict, возвращающую:
  {"sql": str, "params": list}
  где sql — собранная строка SQL, params — список подставленных параметров.

В ответе верни только код одним блоком ```python ... ```, без дополнительных пояснений вне блока.
"""

LEVEL2_PROMPT = """\
Дополни свой SQL-компилятор поддержкой JOIN, GROUP BY и расширенных операторов:

1. Связи (JOINS):
   - joins: список { type?: 'INNER'|'LEFT'|'RIGHT', table: str, on: { <left_col>: <right_col> } }
     (по умолчанию type 'INNER'). Пример: LEFT JOIN items ON orders.id = items.order_id

2. Группировка:
   - groupBy: список колонок (list[str]). Пример: GROUP BY orders.id, orders.status

3. Расширенные операторы в where:
   - op: 'IN', value: list — генерирует field IN ($1, $2, ...)
   - op: 'IS NULL' — генерирует field IS NULL (без плейсхолдера и без добавления в params)
   - op: 'IS NOT NULL' — генерирует field IS NOT NULL (без плейсхолдера и без добавления в params)
   - op: 'LIKE', value: str — генерирует field LIKE $1

Не меняй поведение Level 1 и сохрани сигнатуру compile_query(query: dict) -> dict.

В ответе верни только код одним блоком ```python ... ```, без дополнительных пояснений вне блока.
"""

LEVEL3_PROMPT = """\
Дополни свой SQL-компилятор поддержкой вычисляемых выражений в SELECT, HAVING и подзапросов:

1. Выражения с псевдонимами в select:
   - элемент списка select может быть объектом: { expr: str, as: str }
     Пример: { expr: 'COUNT(items.id)', as: 'item_count' } -> SELECT orders.id, COUNT(items.id) AS item_count

2. Условие HAVING:
   - having (dict, опционально): дерево условий в том же формате, что и where.
     Пример: HAVING SUM(sales.amount) > $1. Параметры из having нумеруются дальше после where.

3. Подзапросы в WHERE:
   - { field: str, op: 'IN', query: dict } — условие с вложенным AST подзапроса.
     Пример: field IN (SELECT user_id FROM vip_members WHERE tier = $1)
     Параметры подзапроса корректно встраиваются в общий список params с правильной сквозной нумерацией плейсхолдеров.

Не меняй поведение Level 1 и Level 2 и сохрани сигнатуру compile_query(query: dict) -> dict.

В ответе верни только код одним блоком ```python ... ```, без дополнительных пояснений вне блока.
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
    """Убирает лишние пробелы из SQL строки."""
    return re.sub(r"\s+", " ", str(s)).strip()


def run_sql_suite(tests: list[tuple[str, dict, dict]], solution_path: str | Path) -> tuple[int, int, list[str]]:
    """Выполняет тестовый набор SQL компилятора и возвращает (passed, total, failures)."""
    passed = 0
    failures: list[str] = []

    for test_name, query, expected in tests:
        success, result = call_with_timeout(str(solution_path), "compile_query", (query,))
        if not success:
            failures.append(f"{test_name}: исключение/таймаут: {result}")
            continue

        if not isinstance(result, dict) or "sql" not in result or "params" not in result:
            failures.append(f"{test_name}: ожидался dict с ключами 'sql' и 'params', получено {result}")
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
                diffs.append(f"SQL: ожидали '{exp_sql}', получили '{res_sql}'")
            if res_params != exp_params:
                diffs.append(f"params: ожидали {exp_params}, получили {res_params}")
            failures.append(f"{test_name}: {'; '.join(diffs)}")

    return passed, len(tests), failures


class SQLBenchmark(Benchmark):
    id = "sql"
    name = "Компилятор SQL AST (SELECT/WHERE/JOIN/GROUP BY/HAVING)"
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
            return TestResult(0, len(tests), [f"не удалось загрузить решение: {e}"])

        passed, total, failures = run_sql_suite(tests, answer_path)
        return TestResult(passed, total, failures)
