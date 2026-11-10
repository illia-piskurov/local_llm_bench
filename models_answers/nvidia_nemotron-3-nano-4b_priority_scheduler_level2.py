import heapq
from typing import Dict, List, Tuple

def plan_order(tasks: Dict[str, Tuple[int, List[str], int]], workers: int) -> List[str] | None:
    all_tasks = set(tasks.keys())
    dur = {t: tasks[t][0] for t in all_tasks}
    preds = {t: tasks[t][1] for t in all_tasks}
    prio = {t: tasks[t][2] for t in all_tasks}

    indeg = {t: 0 for t in all_tasks}
    graph = {}
    for child, deps in preds.items():
        indeg[child] += len(deps)
        for dep in deps:
            graph.setdefault(dep, []).append(child)

    indeg_copy = indeg.copy()
    q = [t for t in all_tasks if indeg_copy[t] == 0]
    order = []
    while q:
        curr = q.pop(0)
        order.append(curr)
        nxts = graph.get(curr, [])
        for child in nxts:
            indeg_copy[child] -= 1
            if indeg_copy[child] == 0:
                q.append(child)

    if len(order) != len(all_tasks):
        return None

    completed = set()
    started = set()
    result: List[str] = []
    events: List[Tuple[int, str, str]] = []  # (time, 'finish', task)
    current_time = 0

    while True:
        ready = [
            t for t in all_tasks
            if not started[t]
            and (not preds[t] or all(d in completed for d in preds[t]))
        ]
        if not ready:
            break

        ready.sort(key=lambda x: (-prio[x], dur[x], x))
        selected = ready[:workers]

        for t in selected:
            result.append(t)
            started.add(t)

        for t in selected:
            heapq.heappush(events, (current_time + dur[t], 'finish', t))

        while events and events[0][0] == current_time:
            _, _, task = heapq.heappop(events)
            completed.add(task)

        if not events:
            break

        next_time = events[0][0]
        current_time = next_time

    return result


def critical_path(tasks: Dict[str, Tuple[int, List[str], int]]) -> int | None:
    all_tasks = set(tasks.keys())
    dur = {t: tasks[t][0] for t in all_tasks}
    preds = {t: tasks[t][1] for t in all_tasks}

    indeg = {t: 0 for t in all_tasks}
    graph = {}
    for child, deps in preds.items():
        indeg[child] += len(deps)
        for dep in deps:
            graph.setdefault(dep, []).append(child)

    indeg_copy = indeg.copy()
    q = [t for t in all_tasks if indeg_copy[t] == 0]
    order = []
    while q:
        curr = q.pop(0)
        order.append(curr)
        nxts = graph.get(curr, [])
        for child in nxts:
            indeg_copy[child] -= 1
            if indeg_copy[child] == 0:
                q.append(child)

    if len(order) != len(all_tasks):
        return None

    # longest path sum of durations using DP on topological order
    dist = {}
    for t in all_tasks:
        deps_dur = [dur[p] for p in preds[t]]
        if not dep_s:
            dist[t] = dur[t]
        else:
            dist[t] = max(dist[p] + dur[p] for p in preds[t])

    return max(dist.values()) if dist else None


def makespan(tasks: Dict[str, Tuple[int, List[str], int]], workers: int) -> int | None:
    all_tasks = set(tasks.keys())
    dur = {t: tasks[t][0] for t in all_tasks}
    preds = {t: tasks[t][1] for t in all_tasks}

    indeg = {t: 0 for t in all_tasks}
    graph = {}
    for child, deps in preds.items():
        indeg[child] += len(deps)
        for dep in deps:
            graph.setdefault(dep, []).append(child)

    indeg_copy = indeg.copy()
    q = [t for t in all_tasks if indeg_copy[t] == 0]
    while q:
        curr = q.pop(0)
        nxts = graph.get(curr, [])
        for child in nxts:
            indeg_copy[child] -= 1
            if indeg_copy[child] == 0:
                q.append(child)

    if len(q) != len(all_tasks):
        return None

    completed = set()
    started = set()
    events: List[Tuple[int, str, str]] = []
    current_time = 0

    while True:
        ready = [
            t for t in all_tasks
            if not started[t]
            and (not preds[t] or all(d in completed for d in preds[t]))
        ]
        if not ready:
            break

        ready.sort(key=lambda x: (-tasks[x][2], tasks[x][0], x))
        selected = ready[:workers]

        for t in selected:
            started.add(t)

        for t in selected:
            heapq.heappush(events, (current_time + dur[t], 'finish', t))

        while events and events[0][0] == current_time:
            _, _, task = heapq.heappop(events)
            completed.add(task)

        if not events:
            break

        next_time = events[0][0]
        current_time = next_time

    return current_time
