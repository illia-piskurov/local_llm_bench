from collections import deque

def has_cycle(task_name, tasks):
    visited = set()
    recursion_stack = set()

    def _has_cycle(name):
        if name in recursion_stack:
            return True
        if name in visited:
            return False

        visited.add(name)
        recursion_stack.add(name)

        duration, deps, _ = tasks[name]
        for dep in deps:
            if _has_cycle(dep):
                return True

        recursion_stack.remove(name)
        return False

    return any(_has_cycle(task) for task in tasks.keys())

def critical_path(tasks: dict[str, tuple[int, list[str], int]]) -> int | None:
    if has_cycle(tasks):
        return None

    # Build dependency graph and reverse adjacency list
    graph = {task: [] for task in tasks}
    reverse_graph = {task: set() for task in tasks}

    for task, (_, deps, _) in tasks.items():
        for dep in deps:
            graph[dep].append(task)
            reverse_graph[task].add(dep)

    # Initialize distances
    dist = {task: 0 for task in tasks}
    queue = deque([task for task in tasks if not reverse_graph[task]])

    while queue:
        current = queue.popleft()
        for neighbor in graph[current]:
            dist[neighbor] = max(dist[neighbor], dist[current] + tasks[neighbor][0])
            if not any(dep in reverse_graph[neighbor] for dep in tasks[neighbor][1]):
                queue.append(neighbor)

    return max(dist.values()) if dist else None

def makespan(tasks: dict[str, tuple[int, list[str], int]], workers: int) -> int | None:
    if has_cycle(tasks):
        return None

    # Initialize data structures
    ready_queue = deque()
    task_info = {task: (duration, deps, priority) for task, (duration, deps, priority) in tasks.items()}
    completed_tasks = set()
    current_time = 0
    active_workers = 0
    output = []

    # Precompute dependencies and ready queue
    for task in tasks:
        duration, deps, _ = task_info[task]
        if not deps:
            ready_queue.append(task)

    while ready_queue or active_workers < workers:
        # Process completed tasks to update ready queue
        while active_workers >= workers and ready_queue:
            task = ready_queue.popleft()
            duration, _, priority = task_info[task]

            all_deps_met = True
            for dep in task_info[task][1]:
                if dep not in completed_tasks:
                    all_deps_met = False
                    break

            if all_deps_met:
                active_workers += 1
                current_time += duration
                output.append(task)
                completed_tasks.add(task)

        # Update ready queue based on completed tasks
        for task in list(completed_tasks):
            duration, deps, _ = task_info[task]
            if not deps:
                continue

            for dep in deps:
                if dep in completed_tasks:
                    ready_queue.append(task)
                    break  # Only add once per dependency completion

        # Sort ready queue by priority, duration, and name
        ready_queue.sort(key=lambda x: (-task_info[x][2], task_info[x][0], x))

    return current_time if output else None
