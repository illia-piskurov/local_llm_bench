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

def critical_path(tasks: dict[str, tuple[int, list[str]]]) -> int | None:
    # Check for cycles using topological sort
    def has_cycle():
        adj = defaultdict(list)
        in_degree = defaultdict(int)
        for task in tasks:
            duration, deps = tasks[task]
            for dep in deps:
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

        return len(result) != len(tasks)

    if has_cycle():
        return None

    # Compute critical path length
    dp = {}
    for task in tasks:
        duration, deps = tasks[task]
        max_prev = 0
        for dep in deps:
            if dep in dp:
                max_prev = max(max_prev, dp[dep])
        dp[task] = duration + max_prev

    return max(dp.values()) if dp else 0
