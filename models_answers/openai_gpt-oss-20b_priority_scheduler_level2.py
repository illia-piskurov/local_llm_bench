import heapq
from collections import defaultdict, deque

def plan_order(tasks: dict[str, tuple[int, list[str], int]], workers: int) -> list[str] | None:
    indeg = {name: 0 for name in tasks}
    dependents = defaultdict(list)
    for name, (_, deps, _) in tasks.items():
        for d in deps:
            if d not in tasks:
                return None
            dependents[d].append(name)
            indeg[name] += 1

    ready = []
    for name, (dur, _, pri) in tasks.items():
        if indeg[name] == 0:
            heapq.heappush(ready, (-pri, dur, name))

    time = 0
    running = []  # (finish_time, name)
    result = []

    while ready or running:
        while workers > 0 and ready:
            pri_neg, dur, name = heapq.heappop(ready)
            finish = time + dur
            heapq.heappush(running, (finish, name))
            result.append(name)
            workers -= 1

        if not running:
            break

        next_finish, _ = running[0]
        time = next_finish

        while running and running[0][0] == time:
            _, finished_name = heapq.heappop(running)
            workers += 1
            for dep in dependents[finished_name]:
                indeg[dep] -= 1
                if indeg[dep] == 0:
                    dur, _, pri = tasks[dep]
                    heapq.heappush(ready, (-pri, dur, dep))

    return result if len(result) == len(tasks) else None

def _topo_order(tasks: dict[str, tuple[int, list[str], int]]) -> list[str] | None:
    indeg = {name: 0 for name in tasks}
    adj = defaultdict(list)
    for name, (_, deps, _) in tasks.items():
        for d in deps:
            if d not in tasks:
                return None
            adj[d].append(name)
            indeg[name] += 1

    q = deque([n for n, d in indeg.items() if d == 0])
    order = []
    while q:
        u = q.popleft()
        order.append(u)
        for v in adj[u]:
            indeg[v] -= 1
            if indeg[v] == 0:
                q.append(v)

    return order if len(order) == len(tasks) else None

def critical_path(tasks: dict[str, tuple[int, list[str], int]]) -> int | None:
    order = _topo_order(tasks)
    if order is None:
        return None
    dp = {name: 0 for name in tasks}
    for name in order:
        dur, deps, _ = tasks[name]
        max_pre = 0
        for d in deps:
            max_pre = max(max_pre, dp[d])
        dp[name] = max_pre + dur
    return max(dp.values())

def makespan(tasks: dict[str, tuple[int, list[str], int]], workers: int) -> int | None:
    order = _topo_order(tasks)
    if order is None:
        return None

    indeg = {name: 0 for name in tasks}
    dependents = defaultdict(list)
    for name, (_, deps, _) in tasks.items():
        for d in deps:
            dependents[d].append(name)
            indeg[name] += 1

    ready = []
    for name, (dur, _, pri) in tasks.items():
        if indeg[name] == 0:
            heapq.heappush(ready, (-pri, dur, name))

    time = 0
    running = []  # (finish_time, name)
    free_workers = workers

    while ready or running:
        while free_workers > 0 and ready:
            pri_neg, dur, name = heapq.heappop(ready)
            finish = time + dur
            heapq.heappush(running, (finish, name))
            free_workers -= 1

        if not running:
            break

        next_finish, _ = running[0]
        time = next_finish

        while running and running[0][0] == time:
            _, finished_name = heapq.heappop(running)
            free_workers += 1
            for dep in dependents[finished_name]:
                indeg[dep] -= 1
                if indeg[dep] == 0:
                    dur, _, pri = tasks[dep]
                    heapq.heappush(ready, (-pri, dur, dep))

    return time if len(running) == 0 else None
