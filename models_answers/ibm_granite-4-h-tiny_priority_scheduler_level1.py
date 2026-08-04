from collections import defaultdict, deque

def plan_order(tasks: dict[str, tuple[int, list[str], int]], workers: int) -> list[str] | None:
    graph = defaultdict(list)
    indegree = {task: 0 for task in tasks}
    duration_map = {}
    priority_map = {}

    for task, (duration, deps, _) in tasks.items():
        duration_map[task] = duration
        priority_map[task] = -_  # invert to use min-heap as max-heap

    for task, (_, deps, _) in tasks.items():
        for dep in deps:
            graph[dep].append(task)
            indegree[task] += 1

    zero_indegree_tasks = deque([task for task in tasks if indegree[task] == 0])
    schedule = []
    current_time = 0
    available_workers = workers

    while zero_indegree_tasks or len(schedule) < len(tasks):
        ready_tasks = [task for task in zero_indegree_tasks if all(indeg_map[dep] == 0 for dep in graph[task])]
        
        if not ready_tasks:
            current_time += 1
            continue
        
        ready_tasks.sort(key=lambda t: (priority_map[t], -duration_map[t], t))
        
        while available_workers > 0 and ready_tasks:
            task = ready_tasks.pop(0)
            schedule.append(task)
            indegree[task] -= 1
            if indegree[task] == 0:
                zero_indegree_tasks.append(task)
            
            available_workers -= 1
        
        current_time += 1
        for task in list(zero_indegree_tasks):
            if all(indeg_map[dep] == 0 for dep in graph[task]):
                zero_indegree_tasks.remove(task)

    return schedule if len(schedule) == len(tasks) else None
