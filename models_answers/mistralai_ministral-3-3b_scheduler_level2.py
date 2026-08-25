from collections import deque

def topo_sort(tasks: dict[str, list[str]]) -> list[str] | None:
    in_degree = {task: 0 for task in tasks}
    graph = {task: [] for task in tasks}

    # Подсчёт степени входа и построение графа
    for task, dependencies in tasks.items():
        for dep in dependencies:
            if dep not in tasks:
                return None  # цикл или несуществующая задача
            graph[dep].append(task)
            in_degree[task] += 1

    # Начальный набор задач без зависимостей
    queue = deque([task for task in in_degree if in_degree[task] == 0])
    result = []

    while queue:
        current = queue.popleft()
        result.append(current)

        for neighbor in graph[current]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    return None if len(result) != len(tasks) else result

def critical_path(tasks: dict[str, tuple[int, list[str]]]) -> int | None:
    # Проверка на циклы с помощью топологической сортировки
    topo_order = topo_sort({task: dep for task, (_, dep) in tasks.items()})
    if topo_order is None:
        return None

    # Вычисление длительностей и смещений задач
    durations = {task: dur for task, (dur, _) in tasks.items()}
    early_start = {task: 0 for task in tasks}
    late_start = {task: 0 for task in tasks}

    # Расчёт ранних стартов (от начальных задач)
    queue = deque([task for task in early_start if early_start[task] == 0])
    while queue:
        current = queue.popleft()
        for neighbor in graph.get(current, []):
            if early_start[neighbor] < early_start[current] + durations[current]:
                early_start[neighbor] = early_start[current] + durations[current]
                queue.append(neighbor)

    # Расчёт поздних стартов (от конечных задач)
    late_end = {task: 0 for task in tasks}
    for task in reversed(topo_order):
        latest_end = max(late_end.get(dep, 0) - durations[dep] for dep in graph.get(task, []) if dep in tasks)
        late_start[task] = latest_end
        late_end[task] = late_start[task] + durations[task]

    # Нахождение критического пути (максимальная разница между ранним и поздним стартом)
    critical_path_length = max(late_start[task] - early_start[task] for task in tasks)

    return critical_path_length if critical_path_length > 0 else None
