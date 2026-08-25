import heapq

def plan_order(tasks: dict[str, tuple[int, list[str], int]], workers: int) -> list[str] | None:
    in_degree = {name: 0 for name in tasks}
    adj = {name: [] for name in tasks}
    
    for name, (duration, deps, priority) in tasks.items():
        in_degree[name] = len(deps)
        for dep in deps:
            if dep in adj:
                adj[dep].append(name)

    ready_queue = []
    for name in tasks:
        if in_degree[name] == 0:
            duration, _, priority = tasks[name]
            heapq.heappush(ready_queue, (-priority, duration, name))
            
    running = []  # List of (end_time, name)
    result = []
    completed_count = 0
    current_time = 0
    
    while completed_count < len(tasks):
        finished_this_step = []
        running.sort()
        
        i = 0
        while i < len(running):
            end_time, name = running[i]
            if end_time <= current_time:
                finished_this_step.append(name)
                running.pop(i)
            else:
                i += 1
        
        for name in finished_this_step:
            completed_count += 1
            for neighbor in adj[name]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    duration, _, priority = tasks[neighbor]
                    heapq.heappush(ready_queue, (-priority, duration, neighbor))
        
        while len(running) < workers and ready_queue:
            neg_prio, dur, name = heapq.heappop(ready_queue)
            running.append((current_time + tasks[name][0], name))
            result.append(name)
            
        if running:
            next_time = min(r[0] for r in running)
            current_time = next_time
        else:
            if completed_count < len(tasks):
                return None
            break
            
    return result

def critical_path(tasks: dict[str, tuple[int, list[str], int]]) -> int | None:
    adj = {name: [] for name in tasks}
    for name, (duration, deps, priority) in tasks.items():
        for dep in deps:
            if dep in adj:
                adj[dep].append(name)
    
    visited = {} # 0: unvisited, 1: visiting, 2: visited
    def has_cycle(u):
        visited[u] = 1
        for v in adj[u]:
            if visited.get(v, 0) == 1: return True
            if visited.get(v, 0) == 0 and has_cycle(v): return True
        visited[u] = 2
        return False
    
    for name in tasks:
        if visited.get(name, 0) == 0:
            if has_cycle(name): return None
            
    memo = {}
    def get_max_path(u):
        if u in memo: return memo[u]
        max_child = 0
        for v in adj[u]:
            max_child = max(max_child, get_max_path(v))
        memo[u] = tasks[u][0] + max_child
        return memo[u]
    
    if not tasks: return 0
    return max(get_max_path(name) for name in tasks)

def makespan(tasks: dict[str, tuple[int, list[str], int]], workers: int) -> int | None:
    if not tasks: return 0
    
    in_degree = {name: 0 for name in tasks}
    adj = {name: [] for name in tasks}
    for name, (duration, deps, priority) in tasks.items():
        in_degree[name] = len(deps)
        for dep in deps:
            if dep in adj:
                adj[dep].append(name)

    ready_queue = []
    for name in tasks:
        if in_degree[name] == 0:
            duration, _, priority = tasks[name]
            heapq.heappush(ready_queue, (-priority, duration, name))
            
    running = []
    completed_count = 0
    current_time = 0
    
    while completed_count < len(tasks):
        finished_this_step = []
        running.sort()
        
        i = 0
        while i < len(running):
            end_time, name = running[i]
            if end_time <= current_time:
                finished_this_step.append(name)
                running.pop(i)
            else:
                i += 1
        
        for name in finished_this_step:
            completed_count += 1
            for neighbor in adj[name]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    duration, _, priority = tasks[neighbor]
                    heapq.heappush(ready_queue, (-priority, duration, neighbor))
        
        while len(running) < workers and ready_queue:
            neg_prio, dur, name = heapq.heappop(ready_queue)
            running.append((current_time + tasks[name][0], name))
            
        if running:
            next_time = min(r[0] for r in running)
            current_time = next_time
        else:
            if completed_count < len(tasks):
                return None
            break
            
    return current_time
