def critical_path(tasks: dict[str, tuple[int, list[str], int]]) -> int | None:
    """
    Длина самого длинного зависимого пути по сумме duration, игнорируя priority.
    Если в графе зависимостей есть цикл — верни None.
    """
    task_map = {task: (duration, deps, priority) for task, (duration, deps, priority) in tasks.items()}
    in_degree = {task: 0 for task in task_map}
    graph = {task: [] for task in task_map}

    for task, (duration, deps, priority) in task_map.items():
        for dep in deps:
            graph[dep].append(task)
            in_degree[task] += 1

    queue = [task for task in task_map if in_degree[task] == 0]
    if not queue:
        return None

    while queue:
        node = queue.pop(0)
        for neighbor in graph[node]:
            in_degree[neighbor] -= 1
            queue.append(neighbor)

    if len(queue) != len(task_map):
        return None

    longest_path = 0
    max_duration = 0
    for node in task_map:
        if in_degree[node] == 0:
            longest_path = max(longest_path, task_map[node][0])
            max_duration = max(max_duration, task_map[node][0])

    return longest_path
def makespan(tasks: dict[str, tuple[int, list[str], int]], workers: int) -> int | None:
    """
    Общее время завершения всех задач при тех же правилах выбора задач, что и в plan_order.
    Используй тот же детерминированный порядок выбора готовых задач:
    priority по убыванию, duration по возрастанию, name по возрастанию.
    Если в графе зависимостей есть цикл — верни None.
    """
    task_map = {task: (duration, deps, priority) for task, (duration, deps, priority) in tasks.items()}
    in_degree = {task: 0 for task in task_map}
    graph = {task: [] for task in task_map}

    for task, (duration, deps, priority) in task_map.items():
        for dep in deps:
            graph[dep].append(task)
            in_degree[task] += 1

    queue = [task for task in task_map if in_degree[task] == 0]
    if not queue:
        return 0

    while queue:
        node = queue.pop(0)
        for neighbor in graph[node]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    if len(queue) != len(task_map):
        return None

    max_time = 0
    for node in task_map:
        if in_degree[node] > max_time:
            max_time = in_degree[node]

    return max_time
