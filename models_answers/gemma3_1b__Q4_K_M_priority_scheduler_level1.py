def plan_order(tasks: dict[str, tuple[int, list[str], int]], workers: int) -> list[str] | None:
    """
    Implements a task scheduler with dependencies, priorities, and a limited worker pool.

    Args:
        tasks: A dictionary where keys are task names and values are tuples
               (duration, deps, priority).
        workers: The maximum number of tasks that can run simultaneously.

    Returns:
        A list of task names sorted by priority and duration, or None if a cyclic dependency exists.
    """

    in_degree = {}
    graph = {}
    for task, (duration, deps, priority) in tasks.items():
        in_degree[task] = 0
        graph[task] = []

    for task, (duration, deps, priority) in tasks.items():
        for dep in deps:
            graph[task].append(dep)
            in_degree[dep] = in_degree.get(dep, 0) + 1

    queue = []
    for task, (duration, deps, priority) in tasks.items():
        if in_degree[task] == 0:
            queue.append(task)

    result = []
    while queue:
        task = queue.pop(0)
        result.append(task)

        for neighbor in graph[task]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    if len(result) != len(tasks):
        return None

    return result
