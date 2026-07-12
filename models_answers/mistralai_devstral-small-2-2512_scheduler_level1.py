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
