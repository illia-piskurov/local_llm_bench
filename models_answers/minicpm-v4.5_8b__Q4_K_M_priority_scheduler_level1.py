from collections import defaultdict, deque
from typing import Dict, Tuple, List, Union

def plan_order(tasks: Dict[str, Tuple[int, List[str], int]], workers: int) -> Union[List[str], None]:
    task_info = {name: (duration, deps, priority) for name, (duration, deps, priority) in tasks.items()}
    task_names = list(task_info.keys())
    in_degree = {name: 0 for name in task_names}
    graph = defaultdict(list)
    for name, (duration, deps, priority) in task_info.items():
        for dep in deps:
            graph[dep].append(name)
            in_degree[name] += 1
    
    if any(in_degree[name] == float('inf') for name in task_names):
        return None
    
    queue = deque([name for name in task_names if in_degree[name] == 0])
    order = []
    while queue:
        if len(queue) > workers:
            return None
        current = []
        for _ in range(min(len(queue), workers)):
            if not queue:
                return None
            name = queue.popleft()
            current.append(name)
            for neighbor in graph[name]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        order.extend(current)
    
    if len(order) != len(task_names):
        return None
    
    schedule = []
    time = 0
    task_durations = {name: duration for name, (duration, _, _) in task_info.items()}
    task_priorities = {name: priority for name, (_, _, priority) in task_info.items()}
    task_names = list(task_info.keys())
    
    while time < max(task_durations.values()):
        ready_tasks = []
        for name in task_names:
            if in_degree[name] == 0 and task_durations[name] > 0:
                ready_tasks.append((task_priorities[name], task_durations[name], name))
        if not ready_tasks:
            return None
        ready_tasks.sort(key=lambda x: (-x[0], x[1], x[2]))
        selected = ready_tasks[:workers]
        for _, duration, name in selected:
            schedule.append(name)
            time += duration
            task_durations[name] -= duration
            for neighbor in graph[name]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    task_names.remove(neighbor)
    
    return schedule
