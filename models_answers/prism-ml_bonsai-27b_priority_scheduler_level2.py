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
    
    # Track running tasks: (end_time, task_name)
    running = []
    completed = set()
    timeline = []
    
    # Initialize ready tasks at time 0
    for task in order:
        if not any(dep in completed for dep in tasks[task][1]):
            heapq.heappush(running, (tasks[task][0], task))
    
    current_time = 0
    
    while running or len(completed) < len(tasks):
        # Advance time to next event
        if not running:
            break
        
        # Process completions at current_time
        while running and running[0][0] <= current_time:
            end_time, task = heapq.heappop(running)
            completed.add(task)
            
            # Add newly ready tasks
            for next_task in graph.get(task, set()):
                if not any(dep in completed for dep in tasks[next_task][1]):
                    heapq.heappush(running, (current_time + tasks[next_task][0], next_task))
        
        current_time += 1
    
    return list(set(timeline))


def critical_path(tasks: dict[str, tuple[int, list[str], int]]) -> int | None:
    if not tasks:
        return 0
    
    # Check for cycles using topological sort
    in_degree = {task: 0 for task in tasks}
    graph = {task: set() for task in tasks}
    
    for task, (_, deps, _) in tasks.items():
        for dep in deps:
            if dep not in tasks:
                return None
            graph[dep].add(task)
            in_degree[task] += 1
    
    queue = [t for t, deg in in_degree.items() if deg == 0]
    
    order = []
    while queue:
        queue.sort(key=lambda t: (-tasks[t][2], tasks[t][0], t))
        task = queue.pop(0)
        order.append(task)
        
        for neighbor in graph[task]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)
    
    if len(order) != len(tasks):
        return None
    
    # Compute longest path using DP on topological order
    dist = {task: tasks[task][0] for task in tasks}
    
    for task in order:
        for neighbor in graph.get(task, set()):
            new_dist = dist[task] + tasks[neighbor][0]
            if new_dist > dist[neighbor]:
                dist[neighbor] = new_dist
    
    return max(dist.values())


def makespan(tasks: dict[str, tuple[int, list[str], int]], workers: int) -> int | None:
    if not tasks:
        return 0
    
    # Check for cycles using topological sort
    in_degree = {task: 0 for task in tasks}
    graph = {task: set() for task in tasks}
    
    for task, (_, deps, _) in tasks.items():
        for dep in deps:
            if dep not in tasks:
                return None
            graph[dep].add(task)
            in_degree[task] += 1
    
    queue = [t for t, deg in in_degree.items() if deg == 0]
    
    order = []
    while queue:
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
    
    # Track running tasks: (end_time, task_name)
    running = []
    completed = set()
    
    # Initialize ready tasks at time 0
    for task in order:
        if not any(dep in completed for dep in tasks[task][1]):
            heapq.heappush(running, (tasks[task][0], task))
    
    current_time = 0
    
    while running or len(completed) < len(tasks):
        # Advance time to next event
        if not running:
            break
        
        # Process completions at current_time
        while running and running[0][0] <= current_time:
            end_time, task = heapq.heappop(running)
            completed.add(task)
            
            # Add newly ready tasks
            for next_task in graph.get(task, set()):
                if not any(dep in completed for dep in tasks[next_task][1]):
                    heapq.heappush(running, (current_time + tasks[next_task][0], next_task))
        
        current_time += 1
    
    return max(end_time for end_time, _ in running) if running else 0
