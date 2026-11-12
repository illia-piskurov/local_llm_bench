from collections import deque, defaultdict

def topo_sort(tasks: dict[str, list[str]]) -> list[str] | None:
    # Compute in-degrees
    in_degree = {task: len(dependencies) for task, dependencies in tasks.items()}
    for task, dependencies in tasks.items():
        for dep in dependencies:
            in_degree[task] -= 1

    # Find tasks with zero in-degree
    queue = deque([task for task, degree in in_degree.items() if degree == 0])
    cycle_detected = False

    while queue:
        # Process a task
        current_task = queue.popleft()
        if current_task in cycle_detected:
            return None  # Cycle detected
        # Decrease in-degree of its dependencies
        for task, dependencies in tasks.items():
            if task != current_task and dependencies[current_task] > 0:
                in_degree[task] -= 1
                if in_degree[task] == 0:
                    queue.append(task)
        # Check for cycle
        if cycle_detected:
            return None

    # If we reach here, no cycle, return sorted tasks
    # (but we need to sort? The problem says topological sort, so we can return the list as is)
    # However, to be safe, we can sort the result
    result = [task for task in tasks]
    return result
