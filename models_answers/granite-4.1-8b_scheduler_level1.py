def topo_sort(tasks: dict[str, list[str]]) -> list[str] | None:
    from collections import defaultdict, deque

    # Создаем граф зависимостей и словарь для подсчета входящих ребер
    graph = defaultdict(list)
    in_degree = {task: 0 for task in tasks}

    # Построение графа и заполнение in_degree
    for task, dependencies in tasks.items():
        for dep in dependencies:
            graph[dep].append(task)
            in_degree[task] += 1

    # Очередь для задач без предшественников
    queue = deque([task for task in in_degree if in_degree[task] == 0])

    result = []

    while queue:
        current_task = queue.popleft()
        result.append(current_task)

        # Уменьшаем входящий индекс для всех смежных задач
        for dependent_task in graph[current_task]:
            in_degree[dependent_task] -= 1
            if in_degree[dependent_task] == 0:
                queue.append(dependent_task)

    # Если результат не содержит всех задач, есть цикл зависимости
    if len(result) != len(tasks):
        return None

    return result
