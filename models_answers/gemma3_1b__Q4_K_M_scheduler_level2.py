def critical_path(tasks: dict[str, tuple[int, list[str]]]) -> int | None:
    """
    Implements a task dependency scheduler in a single Python file.

    Args:
        tasks: A dictionary where each value is a tuple of (duration, dependencies_list).

    Returns:
        The length of the critical path — the total duration of the longest dependent sequence
        of tasks (classic critical path method). If the dependency graph contains a cycle, return None.
    """
    in_degree = {}
    graph = {}
    for task in tasks:
        in_degree[task] = 0
        graph[task] = []

    for task in tasks:
        for dependency in tasks[task][1]:
            graph[dependency].append(task)
            in_degree[task] += 1

    queue = []
    for task in in_degree:
        if in_degree[task] == 0:
            queue.append(task)

    result = 0
    while queue:
        task = queue.pop(0)
        result += 1
        for dependent in graph[task]:
            in_degree[dependent] -= 1
            if in_degree[dependent] == 0:
                queue.append(dependent)

    if len(result) != len(tasks):
        return None

    return result
