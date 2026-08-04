def topo_sort(tasks: dict[str, list[str]]) -> list[str] | None:
    from collections import defaultdict

    # Создаем граф и входной/выходный порядок для каждого узла
    graph = defaultdict(list)
    indegree = {task: 0 for task in tasks}

    # Заполняем граф и индев посторонних задач
    for task, dependencies in tasks.items():
        for dependency in dependencies:
            graph[dependency].append(task)
            indegree[task] += 1

    # Отсортируем начальные задачи (не имеющие зависимостей)
    queue = [task for task in tasks if indegree[task] == 0]
    result = []

    while queue:
        # Убеждаемся, что можем продолжить сортировку без циклов
        if not graph:
            break

        current_task = queue.pop(0)
        result.append(current_task)

        for dependent_task in graph[current_task]:
            indegree[dependent_task] -= 1
            if indegree[dependent_task] == 0:
                queue.append(dependent_task)

        # Удаляем завершенные пути, чтобы избежать циклов
        del graph[current_task]

    # Если все узлы не обработаны, есть цикл в графе
    if len(result) != len(tasks):
        return None

    return result
