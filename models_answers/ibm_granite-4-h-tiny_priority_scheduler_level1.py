from collections import defaultdict, deque

def plan_order(tasks: dict[str, tuple[int, list[str], int]], workers: int) -> list[str] | None:
    graph = defaultdict(list)
    indegree = {task: 0 for task in tasks}
    
    for task, (_, deps, _) in tasks.items():
        for dep in deps:
            graph[dep].append(task)
            indegree[task] += 1
    
    def topological_sort():
        queue = deque([task for task in tasks if indegree[task] == 0])
        sorted_tasks = []
        
        while queue:
            current = min(queue, key=lambda t: (-tasks[t][2], tasks[t][0], t))
            sorted_tasks.append(current)
            queue.remove(current)
            
            for neighbor in graph[current]:
                indegree[neighbor] -= 1
                if indegree[neighbor] == 0:
                    queue.append(neighbor)
        
        return sorted_tasks if len(sorted_tasks) == len(tasks) else None
    
    order = topological_sort()
    
    if not order:
        return None
    
    schedule = []
    current_time = 0
    available_workers = workers
    
    while order or any(indegree[task] == 0 for task in tasks):
        ready_tasks = [task for task in order if indegree[task] == 0]
        
        if not ready_tasks:
            current_time += 1
            continue
        
        ready_tasks.sort(key=lambda t: (-tasks[t][2], tasks[t][0], t))
        
        while available_workers > 0 and ready_tasks:
            task = ready_tasks.pop(0)
            schedule.append((task, current_time))
            
            for neighbor in graph[task]:
                indegree[neighbor] -= 1
            
            if indegree[task] == 0:
                order.remove(task)
        
        current_time += 1
    
    return [task for task, _ in schedule]
