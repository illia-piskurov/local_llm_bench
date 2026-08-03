def plan_order(tasks: dict[str, tuple[int, list[str], int]], workers: int) -> list[str] | None:
    if not tasks:
        return []
    
    # Проверка на циклы и вычисление порядка выполнения (topological sort)
    in_degree = {task: 0 for task in tasks}
    graph = {task: set() for task in tasks}
    
    for task, (_, deps, _) in tasks.items():
        for dep in deps:
            if dep not in tasks:
                return None
            graph[dep].add(task)
            in_degree[task] += 1
    
    # Kahn's algorithm for topological sort with cycle detection
    queue = [t for t, deg in in_degree.items() if deg == 0]
    
    order = []
    while queue:
        # Sort by priority (desc), then duration (asc), then name (asc)
        queue.sort(key=lambda t: (-tasks[t][2], tasks[t][0], t))
        task = queue.pop(0)
        order.append(task)
        
        for neighbor in graph[task]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)
    
    if len(order) != len(tasks):
        return None
    
    # Simulate execution with limited workers
    import heapq
    
    # Events: (time, priority, duration, task_name)
    # We use negative priority for max-heap behavior
    ready_queue = []
    completed = set()
    
    # Initialize ready tasks at time 0
    for task in order:
        if not any(dep in completed for dep in tasks[task][1]):
            heapq.heappush(ready_queue, (-tasks[task][2], tasks[task][0], task))
    
    timeline = []
    current_time = 0
    
    while ready_queue or len(completed) < len(tasks):
        # Advance time to next event if needed
        if not ready_queue:
            if completed == set(tasks.keys()):
                break
            # Find the earliest completion time among running tasks
            # We need to track running tasks separately
            pass
        
        # Process all events at current_time
        while ready_queue and (not timeline or timeline[-1][0] == current_time):
            _, duration, task = heapq.heappop(ready_queue)
            timeline.append(current_time)
            completed.add(task)
        
        if not ready_queue:
            # No more tasks to start, but we might have running ones (handled by completion logic below)
            break
        
        current_time += 1
    
    return list(set(timeline))
