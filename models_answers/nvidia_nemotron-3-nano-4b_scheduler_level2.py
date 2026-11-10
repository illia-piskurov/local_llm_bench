from collections import deque

def topo_sort(tasks: dict[str, list[str]]) -> list[str] | None:
    indegree = {}
    for task in tasks:
        indegree[task] = 0
    for prereq in tasks.values():
        for p in prereq:
            indegree[p] = indegree.get(p, 0) + 1

    zero_indeg = deque([t for t, d in indegree.items() if d == 0])
    order: list[str] = []
    
    while zero_indeg:
        node = zero_indeg.popleft()
        order.append(node)
        for succ, deps in tasks.items():
            if node in deps:
                indegree[succ] -= 1
                if indegree[succ] == 0:
                    zero_indeg.append(succ)

    return None if len(order) != len(tasks) else order


def critical_path(tasks: dict[str, tuple[int, list[str]]]) -> int | None:
    if not tasks:
        return 0

    indegree = {}
    for task in tasks:
        indegree[task] = 0
    for deps in tasks.values():
        for d in deps:
            indegree[d] = indegree.get(d, 0) + 1

    zero_indeg = deque([t for t, d in indegree.items() if d == 0])
    order: list[str] = []
    
    while zero_indeg:
        node = zero_indeg.popleft()
        order.append(node)
        for succ, deps in tasks.items():
            if node in deps:
                indegree[succ] -= 1
                if indegree[succ] == 0:
                    zero_indeg.append(succ)

    # Detect cycle
    if len(order) != len(tasks):
        return None

    finish = {}
    for node in order:
        pred_finish = max(finish[p] for p in tasks[node][1]) if tasks[node][1] else 0
        finish[node] = tasks[node][0] + pred_finish

    return max(finish.values()) if finish else 0
