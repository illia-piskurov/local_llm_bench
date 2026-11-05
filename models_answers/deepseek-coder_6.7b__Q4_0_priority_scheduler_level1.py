import heapq
from collections import defaultdict, deque

def plan_order(tasks: dict[str, tuple[int, list[str], int]], workers: int) -> list[str] | None:
    # Create a graph of tasks and their dependencies
    graph = defaultdict(list)
    in_degree = {task: 0 for task in tasks.keys()}
    for task, (_, deps, _) in tasks.items():
        for dep in deps:
            if dep not in tasks:
                return None
            graph[dep].append(task)
            in_degree[task] += 1

    # Create a priority queue of tasks to be processed
    pq = [(-priority, -duration, task) for task, (duration, _, priority) in tasks.items()]
    heapq.heapify(pq)

    # Process tasks
    res = []
    while pq:
        _, _, task = heapq.heappop(pq)
        res.append(task)
        for neighbor in graph[task]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                duration, deps, priority = tasks[neighbor]
                heapq.heappush(pq, (-priority, -duration, neighbor))

    # If there are still tasks to be processed, there is a cyclic dependency
    if any(degree > 0 for degree in in_degree.values()):
        return None

    return res
