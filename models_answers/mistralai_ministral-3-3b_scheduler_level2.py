import sys
from collections import deque

def critical_path(tasks: dict[str, tuple[int, list[str]]]) -> int | None:
    # Проверяем наличие циклов с помощью топологической сортировки
    topo_result = topo_sort(tasks)

    if topo_result is None:
        return None

    # Инициализация переменных для расчёта
    earliest_start = {task: 0 for task in tasks}
    latest_finish = {}

    # Начальные значения earliest start (для задач без зависимостей)
    for task, deps in tasks.items():
        if not deps:
            earliest_start[task] = deps[0]

    # Рассчитываем earliest start для всех задач
    current_time = 0
    for task in topo_result:
        current_time += tasks[task][0]
        earliest_start[task] = current_time

    # Начальные значения latest finish (с конца)
    for task in reversed(topo_result):
        latest_finish[task] = earliest_start[task]

        # Обновляем latest finish для зависимых задач
        for dependent_task, deps in tasks.items():
            if task in deps:
                latest_finish[dependent_task] = max(latest_finish[dependent_task], latest_finish[task])

    # Определяем длину критического пути
    critical_length = latest_finish[topo_result[-1]]

    return critical_length

# Пример использования (вместе с сохранением в файл)
if __name__ == "__main__":
    tasks = {
        "A": (3, ["B"]),
        "B": (2, ["C"]),
        "C": (1, []),
        "D": (4, ["A", "E"]),
        "E": (2, ["F"]),
        "F": (3, [])
    }

    result = topo_sort(tasks)
    with open("topo_sorted_tasks.txt", "w") as f:
        if result is None:
            print("Граф содержит цикл!", file=f)
        else:
            print("Порядок выполнения:", "\n".join(result), file=f)

    critical_length = critical_path(tasks)
    with open("critical_path.txt", "w") as f:
        if critical_length is None:
            print("Граф содержит цикл!", file=f)
        else:
            print(f"Длина критического пути: {critical_length}", file=f)
