import heapq
from collections import defaultdict, deque

def critical_path(tasks: dict[str, tuple[int, list[str], int]]) -> int | None:
    in_degree = defaultdict(int)
    task_graph = defaultdict(list)
    task_durations = {}
    priority_map = {}

    for task, (duration, deps, priority) in tasks.items():
        task_durations[task] = duration
        priority_map[task] = priority
        for dep in deps:
            task_graph[dep].append(task)
            in_degree[task] += 1

    # Detect cycles using topological sort
    queue = deque([task for task in tasks if in_degree.get(task, 0) == 0])
    visited = set()
    order = []
    while queue:
        current = queue.popleft()
        visited.add(current)
        order.append(current)
        for neighbor in task_graph[current]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    if len(order) != len(tasks):
        return None

    # Reconstruct critical path based on priority and duration
    path = []
    current = max(order)
    while current in tasks:
        for dep in tasks[current][1]:
            if dep in order[:-1] and tasks[dep][0] + task_durations[dep] == task_durations[current] - task_durations[dep[0]]:
                path.append(dep)
                current = dep
                break
    return path

def makespan(tasks: dict[str, tuple[int, list[str], int]], workers: int) -> int | None:
    in_degree = defaultdict(int)
    task_graph = defaultdict(list)
    task_durations = {}
    priority_map = {}

    for task, (duration, deps, priority) in tasks.items():
        task_durations[task] = duration
        priority_map[task] = priority
        for dep in deps:
            task_graph[dep].append(task)
            in_degree[task] += 1

    heap = []
    for task, (_, _, priority) in tasks.items():
        if in_degree.get(task, 0) == 0:
            heapq.heappush(heap, (-priority_map[task], task))

    result = []
    while heap:
        neg_priority, current_task = heapq.heappop(heap)
        result.append(current_task)
        for neighbor in task_graph[current_task]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                heapq.heappush(heap, (-priority_map[neighbor], neighbor))

    if len(result) != len(tasks):
        return None

    # Simulate execution with worker constraints
    completed = 0
    time = 0
    available_workers = workers
    while completed < len(tasks):
        to_assign = []
        for _ in range(min(available_workers, len(result))):
            task = heapq.heappop(heap)[1]
            if all(in_degree[dep] == 0 for dep in tasks[task][1]):
                available_workers -= 1
                completed_task = tasks[task][2]
                time += task_durations[task]
                result.append(task)
                for neighbor in task_graph[task]:
                    in_degree[neighbor] -= 1
        if available_workers > 0:
            heapq.heappush(heap, (-priority_map[result[-1]], result.pop(0)))
    return time
