def topo_sort(tasks: dict[str, list[str]]) -> list[str] | None:
    graph = {task: [] for task in tasks}
    indegree = {task: 0 for task in tasks}
    for task, deps in tasks.items():
        for dep in deps:
            graph[dep].append(task)
            indegree[task] += 1

    queue = [task for task in tasks if indegree[task] == 0]
    result = []
    while queue:
        cur = queue.pop(0)
        result.append(cur)
        for nxt in graph[cur]:
            indegree[nxt] -= 1
            if indegree[nxt] == 0:
                queue.append(nxt)

    if len(result) == len(tasks):
        return result
    else:
        return None

def critical_path(tasks: dict[str, tuple[int, list[str]]]) -> int | None:
    # Build graph and indegree
    graph = {task: [] for task in tasks}
    indegree = {task: 0 for task in tasks}
    for task, (dur, deps) in tasks.items():
        for dep in deps:
            graph[dep].append(task)
            indegree[task] += 1

    # Kahn's algorithm with DP
    queue = [task for task in tasks if indegree[task] == 0]
    dist = {task: 0 for task in tasks}
    processed = 0
    while queue:
        cur = queue.pop(0)
        processed += 1
        cur_dur = tasks[cur][0]
        for nxt in graph[cur]:
            indegree[nxt] -= 1
            if indegree[nxt] == 0:
                queue.append(nxt)
            # Update longest path to nxt
            if dist[nxt] < dist[cur] + tasks[nxt][0]:
                dist[nxt] = dist[cur] + tasks[nxt][0]

    if processed == len(tasks):
        return max(dist.values())
    else:
        return None
