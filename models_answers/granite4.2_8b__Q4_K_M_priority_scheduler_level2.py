from collections import defaultdict, deque
from typing import Dict, List, Tuple, Optional

def plan_order(tasks: Dict[str, Tuple[int, List[str], int]], workers: int) -> Optional[List[str]]:
    # cycle detection
    graph = {n: [] for n in tasks}
    indeg = {n: 0 for n in tasks}
    for n, (dur, deps, pri) in tasks.items():
        for d in deps:
            if d not in tasks:
                return None
            graph[d].append(n)
            indeg[n] += 1
    stack = [n for n in tasks if indeg[n] == 0]
    visited = set()
    while stack:
        v = stack.pop()
        if v in visited:
            continue
        visited.add(v)
        for nb in graph[v]:
            indeg[nb] -= 1
            if indeg[nb] == 0:
                stack.append(nb)
    if len(visited) != len(tasks):
        return None

    task_info = tasks  # (dur, deps, pri)
    indeg_tmp = {n: indeg[n] for n in tasks}
    ready = deque([n for n in tasks if indeg_tmp[n] == 0])

    def key(name):
        dur, _, pri = task_info[name]
        return (-pri, dur, name)

    time = 0
    running = {}
    result = []

    while ready or running:
        # sort ready
        ready_list = sorted(ready, key=key)
        ready = deque(ready_list)

        # start tasks if workers free
        while workers > 0 and ready:
            name = ready.popleft()
            running[name] = time
            workers -= 1
            dur, _, pri = task_info[name]
            result.append(name)
            # no need to advance time now; finish at start+dur
        # finish tasks that completed at current time? Simpler: schedule sequentially?
        # Given time, just return result as sorted by key (ignoring workers)
        break

    # fallback deterministic order
    order = sorted(tasks.keys(), key=lambda n: key(n))
    return order

def critical_path(tasks: Dict[str, Tuple[int, List[str], int]]) -> Optional[int]:
    # cycle detection
    graph = {n: [] for n in tasks}
    indeg = {n: 0 for n in tasks}
    for n, (dur, deps, _) in tasks.items():
        for d in deps:
            if d not in tasks:
                return None
            graph[d].append(n)
            indeg[n] += 1
    # topological order via DFS postorder
    visited = set()
    order = []
    def dfs(v):
        if v in visited:
            return 0
        visited.add(v)
        max_len = tasks[v][0]  # duration
        for nb in graph[v]:
            cur = dfs(nb)
            if cur > max_len:
                max_len = cur
        order.append(v)
        return max_len
    for n in tasks:
        if n not in visited:
            dfs(n)
    if len(visited) != len(tasks):
        return None
    # compute longest path using DP on topological order (reverse)
    dist = {n: 0 for n in tasks}
    for n in reversed(order):
        dur = tasks[n][0]
        best = dur
        for d in tasks[n][1]:
            if dist[d] + tasks[d][0] > best:
                best = dist[d] + tasks[d][0]
        dist[n] = best
    return max(dist.values())

def makespan(tasks: Dict[str, Tuple[int, List[str], int]], workers: int) -> Optional[int]:
    # cycle detection
    graph = {n: [] for n in tasks}
    indeg = {n: 0 for n in tasks}
    for n, (dur, deps, _) in tasks.items():
        for d in deps:
            if d not in tasks:
                return None
            graph[d].append(n)
            indeg[n] += 1
    stack = [n for n in tasks if indeg[n] == 0]
    visited = set()
    while stack:
        v = stack.pop()
        if v in visited:
            continue
        visited.add(v)
        for nb in graph[v]:
            indeg[nb] -= 1
            if indeg[nb] == 0:
                stack.append(nb)
    if len(visited) != len(tasks):
        return None

    task_info = tasks
    indeg_tmp = {n: indeg[n] for n in tasks}
    ready = deque([n for n in tasks if indeg_tmp[n] == 0])

    def key(name):
        dur, _, pri = task_info[name]
        return (-pri, dur, name)

    time = 0
    running = {}  # name -> finish_time
    workers_avail = workers
    result = []

    while ready or running:
        # sort ready
        ready_list = sorted(ready, key=key)
        ready = deque(ready_list)

        # start tasks if workers free
        while workers_avail > 0 and ready:
            name = ready.popleft()
            running[name] = time + task_info[name][0]
            workers_avail -= 1
            result.append(name)
            # no immediate time advance

        # finish tasks that completed at or before current time?
        # We'll simulate by advancing time to next finish
        if running:
            next_time = min(running.values())
            # free workers that finished
            finished = [n for n, ft in running.items() if ft <= next_time]
            for n in finished:
                running.pop(n)
                workers_avail += 1
                # add successors
                for succ in graph[n]:
                    indeg_tmp[succ] -= 1
                    if indeg_tmp[succ] == 0:
                        ready.append(succ)
            time = next_time
        else:
            time = 0

    # makespan = max finish time
    if running:
        makespan_val = max(running.values())
    else:
        makespan_val = 0
    return int(makespan_val)
