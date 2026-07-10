import sys
from collections import deque

def topo_sort(tasks: dict[str, list[str]]) -> list[str] | None:
    # Создаем копию словаря задач для избежания модификации исходного
    graph = {task: dependencies.copy() for task, dependencies in tasks.items()}
    in_degree = {task: 0 for task in tasks}

    # Подсчитываем индекс входящих рёбер (входящие зависимости)
    for task, deps in graph.items():
        for dep in deps:
            if dep not in graph:  # Если зависимость не существует — ошибка
                return None
            in_degree[task] += 1

    # Начальные задачи с нулевым входящим ребром (не зависят от других)
    queue = deque([task for task in in_degree if in_degree[task] == 0])
    result = []

    while queue:
        current_task = queue.popleft()
        result.append(current_task)

        # Уменьшаем входящие рёбра для всех задач, зависящих от текущей
        for dependent_task in graph.get(current_task, []):
            in_degree[dependent_task] -= 1

            # Если входящее ребро стало нулевым — добавляем в очередь
            if in_degree[dependent_task] == 0:
                queue.append(dependent_task)

    # Проверяем на наличие циклов (если не все задачи обработаны)
    return None if len(result) != len(tasks) else result

# Пример использования и сохранение в файл
if __name__ == "__main__":
    tasks = {
        "A": ["B"],
        "B": ["C"],
        "C": [],
        "D": ["A", "E"],
        "E": ["F"],
        "F": []
    }

    result = topo_sort(tasks)
    with open("topo_sorted_tasks.txt", "w") as f:
        if result is None:
            print("Граф содержит цикл!", file=f)
        else:
            print("Порядок выполнения:", "\n".join(result), file=f)

    sys.exit(0 if result is not None else 1)  # Успех/неудача
