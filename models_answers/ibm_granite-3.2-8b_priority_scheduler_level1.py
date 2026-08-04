from collections import defaultdict, deque
from typing import Dict, List, Tuple

def plan_order(tasks: Dict[str, Tuple[int, List[str], int]], workers: int) -> List[str] | None:
    graph = defaultdict(list)
    in_degree = {task: 0 for task in tasks}
    
    # Build the dependency graph
    for task, (_, deps, _) in tasks.items():
        for dep in deps:
            graph[dep].append(task)
            in_degree[task] += 1

    # Check for cycles
    if any(deg > workers for deg in in_degree.values()):
        return None

    # Initialize queues and result list
    ready_queue = deque([task for task in tasks if not in_degree[task]])
    finished_tasks = []
    result = []

    while ready_queue:
        # Select the next task based on priority, duration, and name
        next_tasks = sorted(ready_queue, key=lambda t: (-tasks[t][2], tasks[t][0], t), reverse=True)

        for task in next_tasks[:workers]:
            ready_queue.remove(task)

            # Decrease in-degree of dependent tasks
            for dep in graph[task]:
                in_degree[dep] -= 1
                if in_degree[dep] == 0:
                    ready_queue.append(dep)

            finished_tasks.append(task)
            result.append(task)

    # If all tasks are finished, return the order
    if len(result) == len(tasks):
        return result
    else:
        return None
