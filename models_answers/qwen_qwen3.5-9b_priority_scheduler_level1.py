import heapq
from collections import defaultdict

def plan_order(tasks: dict[str, tuple[int, list[str], int]], workers: int) -> list[str] | None:
    if not tasks:
        return []
    
    task_info = {}
    for name, (duration, deps, priority) in tasks.items():
        task_info[name] = {
            'duration': duration,
            'deps': deps,
            'priority': priority
        }
        
    # Build graph and check cycles using Kahn's algorithm
    adj = defaultdict(list)
    in_degree = {name: 0 for name in tasks}
    
    for name, info in task_info.items():
        for dep in info['deps']:
            if dep not in tasks:
                # Dependency on non-existent task implies it cannot be completed 
                # or is invalid. We treat it as a cycle/blockage to return None.
                pass
            adj[dep].append(name)
            in_degree[name] += 1
            
    queue = [name for name, deg in in_degree.items() if deg == 0]
    processed_count = 0
    
    while queue:
        u = queue.pop(0)
        processed_count += 1
        for v in adj[u]:
            in_degree[v] -= 1
            if in_degree[v] == 0:
                queue.append(v)
                
    if processed_count < len(tasks):
        return None
        
    current_time = 0
    active_tasks = {} # {name: finish_time}
    completed_order = []
    
    while len(completed_order) < len(tasks):
        # 1. Process completions at current_time
        finished_now = []
        for name, finish_time in list(active_tasks.items()):
            if finish_time <= current_time:
                finished_now.append((name, finish_time))
        
        # Sort by priority desc, duration asc, name asc
        finished_now.sort(key=lambda x: (-task_info[x[0]]['priority'], task_info[x[0]]['duration'], x[0]))
        
        for name, _ in finished_now:
            completed_order.append(name)
            del active_tasks[name]
            
        # 2. Advance time if we have active tasks
        if active_tasks:
            current_time = min(active_tasks.values())
            
        # 3. Identify ready tasks (deps satisfied)
        ready_heap = []
        for name, info in task_info.items():
            if name not in completed_order and name not in active_tasks:
                deps_ok = all(dep in completed_order for dep in info['deps'])
                if deps_ok:
                    heapq.heappush(ready_heap, (-info['priority'], info['duration'], name))
                    
        # 4. Start tasks
        slots = workers - len(active_tasks)
        while slots > 0 and ready_heap:
            _, duration, name = heapq.heappop(ready_heap)
            finish_time = current_time + duration
            active_tasks[name] = finish_time
            slots -= 1
            
    return completed_order
