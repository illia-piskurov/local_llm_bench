from collections import defaultdict, deque
import heapq

def plan_order(tasks: dict[str, tuple[int, list[str], int]], workers: int) -> list[str] | None:
    graph = defaultdict(list)
    in_degree = {task: 0 for task in tasks}
    for task, (duration, deps, _) in tasks.items():
        for dep in deps:
            if dep not in tasks:
                return None
            graph[dep].append(task)
            in_degree[task] += 1

    pq = []
    for task, (_, _, priority) in tasks.items():
        heapq.heappush(pq, (-priority, duration, task))

    ready_tasks = deque()
    result = []

    while pq or ready_tasks:
        # Выполнение задач
        for _ in range(min(workers, len(ready_tasks))):
            task = ready_tasks.popleft()
            result.append(task)

        # Добавление новых готовых задач в очередь
        while pq and (-heapq.heappop(pq)[1], task) <= (0, 0) for task in graph if not in_degree[task]]:
            task = graph.popitem()[1][0]
            ready_tasks.append(task)
            in_degree[task] -= 1

    return result
