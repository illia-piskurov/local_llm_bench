from collections import defaultdict, deque
from typing import Dict, List, Tuple

def plan_order(tasks: Dict[str, Tuple[int, List[str], int]], workers: int) -> List[str] | None:
    # Create a graph to store task dependencies
    graph = defaultdict(list)
    # Create a dictionary to store task in-degree
    in_degree = {task: 0 for task in tasks}
    # Create a dictionary to store task duration and priority
    task_info = {task: (duration, priority) for task, (duration, _, priority) in tasks.items()}

    # Build the graph and update in-degree
    for task, (duration, deps, _) in tasks.items():
        for dep in deps:
            graph[dep].append(task)
            in_degree[task] += 1

    # Initialize a queue with tasks that have no dependencies
    queue = deque([task for task in tasks if in_degree[task] == 0])

    # Initialize a list to store the result
    result = []

    # Process tasks in the queue
    while queue:
        # Get the task with the highest priority and shortest duration
        task = max(queue, key=lambda x: (-task_info[x][1], task_info[x][0]))
        # Add the task to the result
        result.append(task)
        # Remove the task from the queue
        queue.remove(task)
        # Update the in-degree of tasks that depend on the current task
        for neighbor in graph[task]:
            in_degree[neighbor] -= 1
            # Add the task to the queue if it has no more dependencies
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    # If there are tasks that have not been processed, it means there is a cyclic dependency
    if len(result) != len(tasks):
        return None

    return result
