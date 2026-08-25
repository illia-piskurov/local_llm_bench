from pathlib import Path

import priority_scheduler_bench
from benchmarks.base import Benchmark, Level, TestResult

LEVEL1_PROMPT = """\
Реализуй планировщик задач с зависимостями, приоритетами и ограниченным числом исполнителей в одном Python файле.

def plan_order(tasks: dict[str, tuple[int, list[str], int]], workers: int) -> list[str] | None

Каждая задача задаётся кортежем (duration, deps, priority):
- duration — длительность задачи в целых единицах времени;
- deps — список имён задач, которые должны завершиться раньше;
- priority — приоритет задачи, чем больше, тем раньше она должна стартовать.

Правила выполнения:
- задачи выполняются не прерываясь;
- одновременно могут идти не более workers задач;
- когда несколько задач готовы к запуску, выбирай сначала с большим priority,
  затем с меньшей duration, затем по имени по возрастанию;
- если несколько задач стартуют в один и тот же момент, возвращай их в list[str]
  в порядке этого же правила;
- если в зависимостях есть цикл, верни None.

В ответе верни только код одним блоком ```python ... ```, без дополнительных пояснений вне блока.
"""

LEVEL2_PROMPT = """\
Дополни свою реализацию двумя функциями:

def critical_path(tasks: dict[str, tuple[int, list[str], int]]) -> int | None

Верни длину самого длинного зависимого пути по сумме duration, игнорируя priority.
Если в графе зависимостей есть цикл — верни None.

def makespan(tasks: dict[str, tuple[int, list[str], int]], workers: int) -> int | None

Верни общее время завершения всех задач при тех же правилах выбора задач, что и в plan_order.
Используй тот же детерминированный порядок выбора готовых задач:
priority по убыванию, duration по возрастанию, name по возрастанию.
Если в графе зависимостей есть цикл — верни None.

Не меняй сигнатуру plan_order.

В ответе верни только код одним блоком ```python ... ```, без дополнительных пояснений вне блока.
"""


class PrioritySchedulerBenchmark(Benchmark):
    id = "priority_scheduler"
    name = "Планировщик с приоритетами и ресурсами"
    short = "PrioSched"
    levels = [
        Level(id="level1", name="Level 1 (plan_order)", prompt=LEVEL1_PROMPT, requires=None),
        Level(id="level2", name="Level 2 (critical_path + makespan)", prompt=LEVEL2_PROMPT, requires="level1"),
    ]

    def run_tests(self, level_id: str, answer_path: Path) -> TestResult:
        if level_id == "level1":
            passed, total, failures = priority_scheduler_bench.run_level1_suite(str(answer_path))
            return TestResult(passed, total, failures)

        passed, total, failures = priority_scheduler_bench.run_level2_suite(str(answer_path))
        return TestResult(passed, total, failures)