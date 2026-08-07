from collections import defaultdict, deque

def plan_order(tasks: dict[str, tuple[int, list[str], int]], workers: int) -> list[str] | None:
    graph = defaultdict(list)
    in_degree = {task: 0 for task in tasks}
    priorities = {}
    
    for name, (duration, deps, priority) in tasks.items():
        priorities[name] = priority
        for dep in deps:
            graph[dep].append(name)
            in_degree[name] += 1
    
    queue = deque([name for name, degree in in_degree.items() if degree == 0])
    
    while queue:
        ready_tasks = []
        while len(ready_tasks) < workers and queue:
            task = queue.popleft()
            # Check if all dependencies are resolved
            if any(task not in [t[0] for t in tasks.values()] for d in graph[task]):
                continue
            ready_tasks.append((priorities[task], -tasks[task][0], task))
        
        if not ready_tasks:
            return None
        
        # Sort by priority (desc), duration (asc), name (asc)
        ready_tasks.sort(key=lambda x: (-x[0], -x[1], x[2]))
        
        for _, _, task in ready_tasks:
            queue.extend([t for t in graph[task] if all(dep in completed for dep in tasks[t][1])])
            in_degree[task] -= 1
            if in_degree[task] == 0:
                queue.append(task)
    
    # Detect cycles by checking if any task is not processed
    if len(tasks) != sum(1 for _ in queue):
        return None
    
    # Return the order of tasks based on priority, duration, and name
    sorted_tasks = sorted((priorities[t], -tasks[t][0], t) for t in tasks)
    return [t[2] for t in sorted_tasks]
