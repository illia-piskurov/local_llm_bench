from collections import deque, defaultdict

def critical_path(tasks: dict[str, tuple[int, list[str]]]) -> int | None:
    # Check for cycles in dependencies
    if critical_path_is_cyclic(tasks):
        return None

    # Compute durations and dependencies for each task
    durations = [duration for (duration, _) in tasks]
    dependencies = [dep for (duration, dep) in tasks]

    # Build graph and compute topological sort
    graph = defaultdict(list)
    in_degree = {task: 0 for task in tasks}
    for task, (duration, dependencies) in tasks:
        for dep in dependencies:
            graph[dep].append(task)
            in_degree[task] += 1

    # Topological sort using Kahn's algorithm
    queue = deque([task for task in in_degree if in_degree[task] == 0])
    topological_order = []
    while queue:
        task = queue.popleft()
        topological_order.append(task)
        for neighbor in graph[task]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    # Calculate path durations
    path_durations = [0] * len(topological_order)
    for task in topological_order:
        for neighbor in graph[task]:
            path_durations[task] = max(path_durations[task], durations[task] + durations[neighbor])

    # Find the critical path (longest path)
    critical_path = max(path_durations, key=lambda x: x)
    return critical_path
