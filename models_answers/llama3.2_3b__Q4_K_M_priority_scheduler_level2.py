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


def critical_path(tasks: Dict[str, Tuple[int, List[str], int]]) -> int | None:
    # Create a graph to store task dependencies
    graph = defaultdict(list)
    # Create a dictionary to store task duration
    task_info = {task: duration for task, (duration, _, _) in tasks.items()}

    # Build the graph
    for task, (duration, deps, _) in tasks.items():
        for dep in deps:
            graph[dep].append(task)

    # Initialize a dictionary to store the longest path length
    longest_path = {task: 0 for task in tasks}

    # Perform DFS to find the longest path
    def dfs(task):
        if task in longest_path:
            return longest_path[task]
        max_path = 0
        for neighbor in graph[task]:
            max_path = max(max_path, dfs(neighbor) + task_info[task])
        longest_path[task] = max_path
        return max_path

    # Find the longest path
    for task in tasks:
        if task not in longest_path:
            longest_path[task] = dfs(task)

    # Find the maximum path length
    max_path = max(longest_path.values())

    # If the maximum path length is infinity, it means there is a cycle
    if max_path == float('inf'):
        return None

    return max_path


def makespan(tasks: Dict[str, Tuple[int, List[str], int]], workers: int) -> int | None:
    # Create a graph to store task dependencies
    graph = defaultdict(list)
    # Create a dictionary to store task duration and priority
    task_info = {task: (duration, priority) for task, (duration, _, priority) in tasks.items()}

    # Build the graph and update in-degree
    for task, (duration, deps, _) in tasks.items():
        for dep in deps:
            graph[dep].append(task)

    # Initialize a dictionary to store the earliest finish time
    earliest_finish = {task: 0 for task in tasks}

    # Initialize a queue with tasks that have no dependencies
    queue = deque([task for task in tasks if earliest_finish[task] == 0])

    # Process tasks in the queue
    while queue:
        # Get the task with the highest priority and shortest duration
        task = max(queue, key=lambda x: (-task_info[x][1], task_info[x][0]))
        # Update the earliest finish time of the task
        earliest_finish[task] = max(earliest_finish[task], earliest_finish[queue[0]] if queue else 0) + task_info[task][0]
        # Remove the task from the queue
        queue.remove(task)
        # Update the in-degree of tasks that depend on the current task
        for neighbor in graph[task]:
            earliest_finish[neighbor] = max(earliest_finish[neighbor], earliest_finish[task])

    # Find the maximum earliest finish time
    max_finish = max(earliest_finish.values())

    # If the maximum earliest finish time is infinity, it means there is a cycle
    if max_finish == float('inf'):
        return None

    return max_finish
