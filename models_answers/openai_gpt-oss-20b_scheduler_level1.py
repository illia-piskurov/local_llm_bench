def topo_sort(tasks: dict[str, list[str]]) -> list[str] | None:
    """
    Return a topological ordering of tasks or None if a cycle exists.
    """
    # Build adjacency list and indegree count
    adj = {task: [] for task in tasks}
    indeg = {task: 0 for task in tasks}

    # Include dependencies that might not be explicit keys
    for deps in tasks.values():
        for dep in deps:
            if dep not in adj:
                adj[dep] = []
                indeg[dep] = 0

    for task, deps in tasks.items():
        for dep in deps:
            adj[dep].append(task)
            indeg[task] += 1

    # Kahn's algorithm
    queue = [t for t, d in indeg.items() if d == 0]
    order = []

    while queue:
        current = queue.pop()
        order.append(current)
        for neighbor in adj[current]:
            indeg[neighbor] -= 1
            if indeg[neighbor] == 0:
                queue.append(neighbor)

    # If all tasks processed, return order; else cycle detected
    if len(order) != len(adj):
        return None
    return order
