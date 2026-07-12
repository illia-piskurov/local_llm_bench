def topo_sort(tasks: dict[str, list[str]]) -> list[str] | None:
    # Построение графа и подсчёт входящих рёбер
    in_degree = {task: 0 for task in tasks}
    graph = {task: [] for task in tasks}

    for task, deps in tasks.items():
        for dep in deps:
            if dep not in graph:
                return None  # зависимость не найдена в задачах
            graph[dep].append(task)
            in_degree[task] += 1

    # Инициализация очереди с нулевой степенью вхождения
    queue = [task for task in in_degree if in_degree[task] == 0]
    result = []

    while queue:
        current = queue.pop(0)
        result.append(current)

        for neighbor in graph[current]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    # Проверка на наличие цикла (если не все задачи были обработаны)
    return result if len(result) == len(tasks) else None

def critical_path(tasks: dict[str, tuple[int, list[str]]]) -> int | None:
    # Сначала получаем топологическую сортировку
    task_names = {name for name in tasks}
    topo_order = topo_sort({name: deps for name, (_, deps) in tasks.items()})
    if topo_order is None or len(topo_order) != len(task_names):
        return None  # цикл в графе

    # Вычисляем earliest start time для каждой задачи
    earliest_start = {task: 0 for task in tasks}
    for task in topo_order:
        max_prev_time = 0
        for dep in tasks[task][1]:
            if earliest_start[dep] + tasks[dep][0] > max_prev_time:
                max_prev_time = earliest_start[dep] + tasks[dep][0]
        earliest_start[task] = max_prev_time

    # Критический путь — максимальное значение earliest start + длительность задачи
    return max(earliest_start[task] + tasks[task][0] for task in tasks) if tasks else 0
