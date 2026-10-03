def topo_sort(tasks: dict[str, list[str]]) -> list[str] | None:
    # Build indegree map and adjacency list
    indeg = {t: 0 for t in tasks}
    graph = {}
    for task, deps in tasks.items():
        graph[task] = []
        for d in deps:
            if d not in tasks:   # ignore invalid dependencies
                continue
            indeg[task] += 1
            graph.setdefault(d, []).append(task)

    # Kahn's algorithm using a list as queue (FIFO)
    queue = [t for t in tasks if indeg[t] == 0]
    order = []
    while queue:
        u = queue.pop(0)          # arbitrary order among independent tasks
        order.append(u)
        for v in graph.get(u, []):
            indeg[v] -= 1
            if indeg[v] == 0:
                queue.append(v)

    return order if len(order) == len(tasks) else None
