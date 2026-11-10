import heapq
from typing import Dict, List, Tuple

def plan_order(tasks: Dict[str, Tuple[int, List[str], int]], workers: int) -> List[str] | None:
    all_tasks = set(tasks.keys())
    dur = {t: tasks[t][0] for t in all_tasks}
    preds = {t: tasks[t][1] for t in all_tasks}
    prio = {t: tasks[t][2] for t in all_tasks}

    # Build graph and compute indegrees for cycle detection
    indeg = {t: 0 for t in all_tasks}
    graph = {}
    for child, deps in preds.items():
        indeg[child] += len(deps)
        for dep in deps:
            graph.setdefault(dep, []).append(child)

    # Kahn's algorithm to detect cycles
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

        # Choose up to workers tasks: priority > duration < name
        ready.sort(key=lambda x: (-prio[x], dur[x], x))
        selected = ready[:workers]

        for t in selected:
            result.append(t)
            started.add(t)

        # Schedule finish events
        for t in selected:
            heapq.heappush(events, (current_time + dur[t], 'finish', t))

        # Process all finishes at current_time
        while events and events[0][0] == current_time:
            _, _, task = heapq.heappop(events)
            completed.add(task)

        if not events:
            break

        next_time = events[0][0]
        current_time = next_time

    return result
