def plan_order(tasks: dict[str, tuple[int, list[str], int]], workers: int) -> list[str] | None:
    indeg = {t: 0 for t in tasks}
    for deps in tasks.values():
        indeg.update(deps)
    rem = {t: d for t, (d, _, _) in tasks.items()}
    total = len(tasks)
    completed = 0
    order = []
    running = set()
    ready = []                     # heap key = (-priority, duration, name)

    import heapq
    for t in indeg:
        if indeg[t] == 0:
            d, priority, name = tasks[t]
            heapq.heappush(ready, (-priority, d, name))

    while completed < total:
        # finish tasks that have remaining time == 1
        to_remove = [t for t in list(running) if rem[t] == 1]
        for t in to_remove:
            running.remove(t)
            completed += 1
            d, priority, name = tasks[t]
            for dep in tasks[t][1]:
                indeg[dep] -= 1
                if indeg[dep] == 0 and dep not in running:
                    heapq.heappush(ready, (-priority, d, dep))

        # start new tasks up to the worker limit
        while len(running) < workers and ready:
            _, dur, name = heapq.heappop(ready)
            running.add(name)
            order.append(name)
            rem[name] = dur

    return None if completed != total else order


def critical_path(tasks: dict[str, tuple[int, list[str], int]]) -> int | None:
    indeg = {t: 0 for t in tasks}
    graph = {}
    for t, (_, deps, _) in tasks.items():
        indeg[t] = len(deps)
        if deps:
            p = deps[0]
            graph.setdefault(p, []).append(t)

    q = [t for t, c in indeg.items() if c == 0]
    dp = {}
    max_len = 0
    while q:
        u = q.pop(0)
        d, _, _ = tasks[u]
        dp[u] = d
        max_len = max(max_len, dp[u])
        for v in graph.get(u, []):
            indeg[v] -= 1
            if indeg[v] == 0:
                q.append(v)
                dp[v] = dp[u] + tasks[v][0]
    return None if len(dp) != len(tasks) else max_len


def makespan(tasks: dict[str, tuple[int, list[str], int]], workers: int) -> int | None:
    import heapq
    indeg = {t: 0 for t in tasks}
    for deps in tasks.values():
        indeg.update(deps)

    ready = []
    for t, c in indeg.items():
        if c == 0:
            d, priority, name = tasks[t]
            heapq.heappush(ready, (-priority, d, name, 0))

    workers_free = [0] * workers
    max_finish = 0
    order = []

    while ready or any(f > 0 for f in workers_free):
        if ready:
            neg_p, dur, name, ready_time = heapq.heappop(ready)
            min_free = min(workers_free)          # earliest free worker
            start = max(ready_time, min_free)
            finish = start + dur
            max_finish = max(max_finish, finish)
            order.append(name)

            idx = workers_free.index(min_free)
            workers_free[idx] = finish

        else:
            break

    return None if len(order) != len(tasks) else max_finish
