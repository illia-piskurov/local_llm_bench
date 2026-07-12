import heapq

def plan_order(tasks: dict[str, tuple[int, list[str], int]], workers: int) -> list[str] | None:
    # 1. Cycle Detection using Kahn's Algorithm
    in_degree = {name: len(deps) for name, (dur, deps, prio) in tasks.items()}
    graph = {name: [] for name in tasks}
    for name, (dur, deps, prio) in tasks.items():
        for d in deps:
            if d in graph:
                graph[d].append(name)
    
    temp_in_degree = in_degree.copy()
    queue = [n for n in tasks if temp_in_degree[n] == 0]
    count = 0
    while queue:
        u = queue.pop(0)
        count += 1
        for v in graph[u]:
            temp_in_degree[v] -= 1
            if temp_in_degree[v] == 0:
                queue.append(v)
    
    if count < len(tasks):
        return None

    # 2. Simulation of the scheduling process
    result = []
    # ready_pool contains tasks whose dependencies are met and haven't started yet
    ready_pool = [name for name, (dur, deps, prio) in tasks.items() if not deps]
    # running is a min-heap of (finish_time, task_name)
    running = [] 
    current_time = 0
    started_count = 0
    total_tasks = len(tasks)

    while started_count < total_tasks:
        # Sort the ready pool by priority (desc), then duration (asc), then name (asc)
        ready_pool.sort(key=lambda x: (-tasks[x][2], tasks[x][0], x))
        
        # Try to start as many tasks as possible from the current pool
        while len(running) < workers and ready_pool:
            task_name = ready_pool.pop(0)
            result.append(task_name)
            finish_time = current_time + tasks[task_name][0]
            heapq.heappush(running, (finish_time, task_name))
            started_count += 1
        
        if running:
            # Advance time to the next completion event
            next_time = running[0][0]
            current_time = next_time
            
            # Process all tasks that finish at this exact moment
            while running and running[0][0] == current_time:
                _, name = heapq.heappop(running)
                for neighbor in graph[name]:
                    in_degree[neighbor] -= 1
                    if in_degree[neighbor] == 0:
                        ready_pool.append(neighbor)
                        
    return result
