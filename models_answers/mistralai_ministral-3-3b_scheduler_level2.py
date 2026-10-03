from collections import deque

def topo_sort(tasks: dict[str, list[str]]) -> list[str] | None:
    adj = {task: [] for task in tasks}
    in_degree = {task: 0 for task in tasks}

    for task, deps in tasks.items():
        for dep in deps:
            if dep not in adj:
                return None
            adj[dep].append(task)
            in_degree[task] += 1

    queue = deque([task for task in tasks if in_degree[task] == 0])
    result = []

    while queue:
        current = queue.popleft()
        result.append(current)

        for neighbor in adj[current]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    return None if len(result) != len(tasks) else result

def critical_path(tasks: dict[str, tuple[int, list[str]]]) -> int | None:
    # Check for cycles using topological sort
    adj = {task: [] for task in tasks}
    in_degree = {task: 0 for task in tasks}

    for task, (_, deps) in tasks.items():
        for dep in deps:
            if dep not in adj:
                return None
            adj[dep].append(task)
            in_degree[task] += 1

    queue = deque([task for task in tasks if in_degree[task] == 0])
    topo_order = []
    while queue:
        current = queue.popleft()
        topo_order.append(current)

        for neighbor in adj[current]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    if len(topo_order) != len(tasks):
        return None

    # Calculate earliest start and finish times
    earliest_start = {task: 0 for task in tasks}
    earliest_finish = {task: 0 for task in tasks}

    for task in reversed(topo_order):
        duration, deps = tasks[task]
        earliest_start[task] = max(earliest_finish[d] for d in deps) if deps else 0
        earliest_finish[task] = earliest_start[task] + duration

    # Find the longest path (critical path)
    critical_length = max(earliest_finish.values())
    return critical_length
