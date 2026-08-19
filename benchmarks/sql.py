from pathlib import Path

import sql_bench
from benchmarks.base import Benchmark, Level, TestResult

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
   - groupBy: список колонок (например, ['orders.id', 'orders.total']) -> GROUP BY orders.id, orders.total

3. Расширенные операторы WHERE:
   - IS NULL / IS NOT NULL: например, { field: 'deleted_at', op: 'IS NULL' } -> генерирует deleted_at IS NULL и НЕ добавляет параметр в params.
   - IN (список значений): например, { field: 'id', op: 'IN', value: [10, 20, 30] } -> генерирует id IN ($1, $2, $3) и добавляет каждый элемент в params.
   - LIKE: например, { field: 'email', op: 'LIKE', value: '%@example.com' } -> email LIKE $1

Не меняй поведение уже реализованных конструкций и сохрани сигнатуру compile_query(query: dict) -> dict.

В ответе верни только код одним блоком ```python ... ```, без дополнительных пояснений вне блока.
"""

LEVEL3_PROMPT = """\
Дополни свой SQL-компилятор поддержкой алиасов выражений в SELECT, условий HAVING и вложенных подзапросов:

1. Алиасы выражений в SELECT:
   - Элемент в select может быть объектом { expr: str, as: str }
     Пример: { expr: "COUNT(items.id)", as: "item_count" } -> COUNT(items.id) AS item_count

2. Условия HAVING:
   - having: объект условия (аналогичный where) -> добавляет секцию HAVING ... после GROUP BY, с параметризацией $n.

3. Вложенные подзапросы (Subqueries) в WHERE:
   - Условие IN с подзапросом: { field: str, op: 'IN', query: dict }
     Пример: { field: "id", op: "IN", query: { table: "vip_members", select: ["user_id"], where: { field: "tier", op: "=", value: "gold" } } }
     -> id IN (SELECT user_id FROM vip_members WHERE tier = $1)
   - Параметры подзапроса должны сквозным образом нумероваться и попадать в общий список params в порядке обхода.

Не меняй поведение уже реализованных конструкций и сохрани сигнатуру compile_query(query: dict) -> dict.

В ответе верни только код одним блоком ```python ... ```, без дополнительных пояснений вне блока.
"""


class SQLBenchmark(Benchmark):
    id = "sql"
    name = "Компилятор SQL AST (compile_query)"
    short = "SQL"
    levels = [
        Level(id="level1", name="Level 1 (SELECT/WHERE/ORDER BY/LIMIT/OFFSET/$1..$n)", prompt=LEVEL1_PROMPT, requires=None),
        Level(id="level2", name="Level 2 (JOIN/GROUP BY/IN/LIKE/IS NULL)", prompt=LEVEL2_PROMPT, requires="level1"),
        Level(id="level3", name="Level 3 (COUNT AS cnt/HAVING/Subqueries)", prompt=LEVEL3_PROMPT, requires="level2"),
    ]

    def run_tests(self, level_id: str, answer_path: Path) -> TestResult:
        if level_id == "level1":
            tests = sql_bench.LEVEL1_TESTS
        elif level_id == "level2":
            tests = sql_bench.LEVEL1_TESTS + sql_bench.LEVEL2_TESTS
        else:
            tests = sql_bench.LEVEL1_TESTS + sql_bench.LEVEL2_TESTS + sql_bench.LEVEL3_TESTS
        name = self.level_by_id(level_id).name
        try:
            sql_bench.load_compile_query(str(answer_path))
        except Exception as e:
            return TestResult(0, len(tests), [f"не удалось загрузить решение: {e}"])
        passed, total, failures = sql_bench.run_suite(name, tests, str(answer_path))
        return TestResult(passed, total, failures)
