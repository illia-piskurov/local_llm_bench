def topo_sort(tasks: dict[str, list[str]]) -> list[str] | None:
    from collections import defaultdict

    graph = defaultdict(list)
    in_degree = {task: 0 for task in tasks}

    # Build the graph and calculate in-degrees
    for task, deps in tasks.items():
        for dep in deps:
            if dep not in in_degree:
                return None  # Invalid dependency
            graph[dep].append(task)
            in_degree[task] += 1

    queue = [task for task, degree in in_degree.items() if degree == 0]
    result = []

    while queue:
        current = queue.pop(0)
        result.append(current)

        for neighbor in graph[current]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    return result if len(result) == len(tasks) else None
