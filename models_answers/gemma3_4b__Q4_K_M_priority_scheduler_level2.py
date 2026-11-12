def plan_order(tasks: dict[str, tuple[int, list[str], int]], workers: int) -> list[str] | None:
    """
    Implements a task scheduler with dependencies, priorities, and a limited worker pool.
    """
    task_names = list(tasks.keys())
    ready_tasks = []
    running_tasks = []
    completed_tasks = []
    time = 0
    task_status = {task: "ready" for task in task_names}
    task_start_time = {task: -1 for task in task_names}

    while ready_tasks or running_tasks:
        # Add ready tasks to the running tasks
        for task_name in list(task_status):
            if task_status[task_name] == "ready":
                deps_met = all(dep in completed_tasks for dep in tasks[task_name][1])
                if deps_met:
                    ready_tasks.append((task_name, tasks[task_name][0], tasks[task_name][2]))
                    task_status[task_name] = "running"
                    task_start_time[task_name] = time

        # Sort running tasks based on priority, duration, and name
        running_tasks = sorted(running_tasks, key=lambda x: (x[2], x[1], x[0]))

        # Remove completed tasks
        completed_tasks = [task for task in running_tasks if task_status[task] != "running"]
        running_tasks = [task for task in running_tasks if task_status[task] == "running"]

        # Limit the number of running tasks
        num_running = len(running_tasks)
        if num_running > workers:
            running_tasks = running_tasks[:workers]

        # Advance time
        time += 1

        # Update task status
        for task_name in running_tasks:
            task_status[task_name] = "running"

        # Mark tasks as complete
        for task_name in running_tasks:
            if time - task_start_time[task_name] == tasks[task_name][0]:
                completed_tasks.append(task_name)
                task_status[task_name] = "completed"

    # Check for cyclic dependencies
    if any(task_status[task] != "completed" for task in task_names):
        return None

    return completed_tasks


def critical_path(tasks: dict[str, tuple[int, list[str], int]]) -> int | None:
    """
    Return the length of the longest dependency path by sum of durations, ignoring priority.
    If there is a cycle in the dependency graph, return None.
    """
    task_names = list(tasks.keys())
    graph = {task: [] for task in task_names}
    for task, (duration, deps, _) in tasks.items():
        for dep in deps:
            graph[dep].append(task)

    def dfs(node, path_length):
        nonlocal has_cycle
        if has_cycle:
            return
        if node in visited:
            return

        visited.add(node)
        path.append(node)

        for neighbor in graph[node]:
            dfs(neighbor, path_length + tasks[neighbor][0])

        visited.remove(node)
        path.pop()

    has_cycle = False
    visited = set()
    path = []

    for task in task_names:
        if task not in visited:
            dfs(task, 0)

    if has_cycle:
        return None

    if not path:
        return 0

    return max(path_length for path_length in path)


def makespan(tasks: dict[str, tuple[int, list[str], int]], workers: int) -> int | None:
    """
    Return the total completion time of all tasks using the same scheduling rules as plan_order.
    Use the same deterministic tie-breaking for ready tasks:
    descending priority, ascending duration, alphabetical name.
    If there is a cycle in the dependency graph, return None.
    """
    result = plan_order(tasks, workers)
    if result is None:
        return None

    completion_times = {}
    for task in result:
        completion_times[task] = completion_times.get(task, 0) + tasks[task][0]

    return max(completion_times.values())
