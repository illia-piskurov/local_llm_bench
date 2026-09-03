from collections import defaultdict, deque

def topo_sort(tasks: dict[str, list[str]]) -> list[str] | None:
    adj = defaultdict(list)
    in_degree = defaultdict(int)

    for task in tasks:
        for dep in tasks[task]:
            adj[dep].append(task)
            in_degree[task] += 1

    queue = deque()
    result = []

    for task in tasks:
        if in_degree[task] == 0:
            queue.append(task)

    while queue:
        u = queue.popleft()
        result.append(u)
        for v in adj[u]:
            in_degree[v] -= 1
            if in_degree[v] == 0:
                queue.append(v)

    return result if len(result) == len(tasks) else None
