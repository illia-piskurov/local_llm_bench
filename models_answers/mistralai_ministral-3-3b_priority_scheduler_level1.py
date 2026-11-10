from collections import defaultdict, deque

def plan_order(tasks: dict[str, tuple[int, list[str], int]], workers: int) -> list[str] | None:
    # Check for cyclic dependencies
    visited = set()
    recursion_stack = set()

    def has_cycle(task):
        if task in recursion_stack:
            return True
        if task in visited:
            return False

        visited.add(task)
        recursion_stack.add(task)

        for dep in tasks.get(task, (0, [], 0))[1]:
            if has_cycle(dep):
                return True

        recursion_stack.remove(task)
        return False

    for task in tasks:
        if has_cycle(task):
            return None

    # Initialize data structures
    ready_queue = deque()
    task_info = {task: (duration, deps, priority) for task, (duration, deps, priority) in tasks.items()}
    completed_tasks = set()
    current_time = 0
    worker_count = 0
    output = []

    # Precompute dependencies and ready queue
    dependency_graph = defaultdict(list)
    in_degree = {task: 0 for task in tasks}
    for task, (_, deps, _) in tasks.items():
        for dep in deps:
            dependency_graph[dep].append(task)
            in_degree[task] += 1

    # Initialize ready queue with tasks having no dependencies
    for task in tasks:
        if in_degree.get(task, 0) == 0:
            ready_queue.append((-task_info[task][2], -task_info[task][0], task))

    while ready_queue or worker_count < workers:
        # Sort ready queue by priority (desc), duration (asc), then name
        current_ready = sorted(ready_queue, key=lambda x: (-x[0], x[1], x[2]))

        if not current_ready and worker_count == 0:
            break

        # Process tasks in order of priority, duration, name
        for _, _, task in current_ready[:workers]:
            if task in completed_tasks or in_degree.get(task, 0) > 0:
                continue

            # Assign this task to a worker
            worker_count += 1
            start_time = current_time
            end_time = start_time + task_info[task][0]

            # Update dependencies
            for dep in task_info[task][1]:
                in_degree[dep] -= 1
                if in_degree.get(dep, 0) == 0:
                    ready_queue.append((-task_info[dep][2], -task_info[dep][0], dep))

            # Update current time to end_time of this task
            current_time = max(current_time, end_time)
            output.append(task)

        # Remove completed tasks from in_degree (they are no longer ready)
        for task in list(completed_tasks):
            if task_info[task][1]:  # If it has dependencies left
                for dep in task_info[task][1]:
                    in_degree[dep] -= 1
                    if in_degree.get(dep, 0) == 0:
                        ready_queue.append((-task_info[dep][2], -task_info[dep][0], dep))

        # Remove completed tasks from output (if any)
        completed_tasks.update(task for task in output[-workers:] if task not in completed_tasks)

    return sorted(output) if current_time >= max(duration for _, duration, _ in tasks.values()) else None
