from typing import Optional

def plan_order(tasks: dict[str, tuple[int, list[str], int]], workers: int) -> list[str] | None:
    if workers <= 0:
        return None
    if not tasks:
        return []

    graph = {}
    for name, (duration, deps, priority) in tasks.items():
        graph[name] = list(deps)

    # Validate dependencies and detect cycles with Kahn's algorithm.
    in_degree = {name: 0 for name in tasks}
    for name, deps in graph.items():
        for dep in deps:
            if dep not in tasks:
                return None
            in_degree[name] += 1

    queue = [name for name in tasks if in_degree[name] == 0]
    order = []
    while queue:
        name = queue.pop(0)
        order.append(name)
        for dep in graph[name]:
            in_degree[dep] -= 1
            if in_degree[dep] == 0:
                queue.append(dep)

    if len(order) != len(tasks):
        return None

    ready = [name for name in tasks if not graph[name]]
    heap = [(-priority, duration, name) for name, (_, _, priority) in tasks.items()]
    import heapq
    heapq.heapify(heap)

    running: dict[str, tuple[int, int]] = {}
    result: list[str] = []
    time = 0

    while running:
        picked = []
        for _ in range(workers):
            if not heap:
                break
            picked.append(heapq.heappop(heap))

        for _, duration, name in picked:
            running[name] = (time, duration)
            result.append(name)

        time += min(duration for _, duration in running.values())

        finished = [name for name, (start, duration) in running.items() if start + duration <= time]
        for name in finished:
            duration, priority = tasks[name][0], tasks[name][2]
            del running[name]
            heapq.heappush(heap, (-priority, duration, name))

    return result
