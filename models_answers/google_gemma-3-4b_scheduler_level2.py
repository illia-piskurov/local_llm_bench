def topo_sort(tasks: dict[str, list[str]]) -> list[str] | None:
    """
    Выполняет топологическую сортировку задач с зависимостями.

    Args:
        tasks (dict): Словарь, где ключ - имя задачи, а значение - список зависимых задач.

    Returns:
        list[str]: Список имён задач в порядке топологической сортировки или None, если есть цикл.
    """
    in_degree = {}
    for task in tasks:
        in_degree[task] = 0
    for task in tasks:
        for dependency in tasks[task]:
            if dependency in in_degree:
                in_degree[task] += 1
            else:
                return None

    queue = []
    for task in in_degree:
        if in_degree[task] == 0:
            queue.append(task)

    result = []
    while queue:
        task = queue.pop(0)
        result.append(task)
        for dependent in tasks:
            if task in tasks[dependent]:
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)

    if len(result) != len(tasks):
        return None
    else:
        return result


def critical_path(tasks: dict[str, tuple[int, list[str]]]) -> int | None:
    """
    Вычисляет длину критического пути.

    Args:
        tasks (dict): Словарь, где значение - кортеж (длительность_задачи, список_зависимостей).

    Returns:
        int: Длина критического пути или None, если есть цикл.
    """
    sorted_tasks = topo_sort(tasks)
    if sorted_tasks is None:
        return None

    distances = {}
    for task in tasks:
        distances[task] = 0

    for task in sorted_tasks:
        duration, dependencies = tasks[task]
        max_dependency_distance = 0
        for dependency in dependencies:
            if dependency in distances:
                max_dependency_distance = max(max_dependency_distance, distances[dependency])
        distances[task] = max_dependency_distance + duration

    return max(distances.values())
