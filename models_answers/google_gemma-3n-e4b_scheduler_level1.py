def topo_sort(tasks: dict[str, list[str]]) -> list[str] | None:
    """
    Реализует топологическую сортировку задач с зависимостями.

    Args:
        tasks: Словарь, где ключ - имя задачи (строка), а значение - список имён задач,
               от которых она зависит (эти задачи должны быть выполнены раньше).

    Returns:
        Список имён всех задач в порядке, при котором каждая задача идёт строго после всех своих зависимостей.
        Если в графе зависимостей есть цикл - возвращает None.
    """

    in_degree = {}
    for task in tasks:
        in_degree[task] = 0
    for task in tasks:
        for dependency in tasks[task]:
            if dependency in in_degree:
                in_degree[task] += 1
            else:
                in_degree[task] = 1

    queue = []
    for task in in_degree:
        if in_degree[task] == 0:
            queue.append(task)

    result = []
    while queue:
        task = queue.pop(0)
        result.append(task)

        for dependent_task in tasks:
            if task in tasks[dependent_task]:
                in_degree[dependent_task] -= 1
                if in_degree[dependent_task] == 0:
                    queue.append(dependent_task)

    if len(result) != len(tasks):
        return None  # Цикл обнаружен
    else:
        return result
