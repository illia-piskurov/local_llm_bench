from pathlib import Path

import scheduler_bench
from benchmarks.base import Benchmark, Level, TestResult

LEVEL1_PROMPT = """\
Реализуй планировщик задач с зависимостями в одном Python файле.

def topo_sort(tasks: dict[str, list[str]]) -> list[str] | None

tasks — словарь, где ключ — имя задачи (строка), а значение — список имён задач,
от которых она зависит (эти задачи должны быть выполнены раньше).

Функция должна вернуть список имён всех задач в порядке, при котором каждая задача
идёт строго после всех своих зависимостей (топологическая сортировка).
Если в графе зависимостей есть цикл — верни None.

Требования:
- Один файл, без внешних зависимостей (никаких networkx и т.п.).
- Порядок среди задач, не зависящих друг от друга, может быть любым — важно только,
  чтобы зависимости шли раньше зависимых от них задач.

В ответе верни только код одним блоком ```python ... ```, без дополнительных пояснений вне блока.
"""

LEVEL2_PROMPT = """\
Дополни свою реализацию функцией расчёта критического пути:

def critical_path(tasks: dict[str, tuple[int, list[str]]]) -> int | None

tasks — словарь, где значение — кортеж (длительность_задачи, список_зависимостей).
Функция должна вернуть длину критического пути — суммарную длительность самой долгой
по времени цепочки зависимых друг от друга задач (classic critical path method).
Если в графе зависимостей есть цикл — верни None.

Не меняй сигнатуру и поведение topo_sort.

В ответе верни только код одним блоком ```python ... ```, без дополнительных пояснений вне блока.
"""


class SchedulerBenchmark(Benchmark):
    id = "scheduler"
    name = "Планировщик задач (topo sort + critical path)"
    short = "Scheduler"
    levels = [
        Level(id="level1", name="Level 1 (topo_sort + циклы)", prompt=LEVEL1_PROMPT, requires=None),
        Level(id="level2", name="Level 2 (critical_path)", prompt=LEVEL2_PROMPT, requires="level1"),
    ]

    def run_tests(self, level_id: str, answer_path: Path) -> TestResult:
        func_name = "topo_sort" if level_id == "level1" else "critical_path"
        tests = scheduler_bench.LEVEL1_TESTS if level_id == "level1" else scheduler_bench.LEVEL2_TESTS
        try:
            scheduler_bench.load_function(str(answer_path), func_name)
        except Exception as e:
            return TestResult(0, len(tests), [f"не удалось загрузить решение: {e}"])

        if level_id == "level1":
            passed, total, failures = scheduler_bench.run_level1_suite(str(answer_path))
        else:
            passed, total, failures = scheduler_bench.run_level2_suite(str(answer_path))
        return TestResult(passed, total, failures)
