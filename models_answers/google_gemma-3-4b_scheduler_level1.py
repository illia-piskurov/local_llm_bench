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
