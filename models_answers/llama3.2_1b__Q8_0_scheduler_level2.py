from collections import defaultdict, deque

def topo_sort(tasks: dict[str, list[str]]) -> list[str] | None:
    graph = defaultdict(list)
    in_degree = {task: 0 for task in tasks}
    
    for task, dependencies in tasks.items():
        for dependency in dependencies:
            graph[dependency].append(task)
            in_degree[task] += 1
    
    queue = deque([task for task in tasks if in_degree[task] == 0])
    
    sorted_tasks = []
    
    while queue:
        task = queue.popleft()
        sorted_tasks.append(task)
        
        for neighbor in graph[task]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)
    
    if len(sorted_tasks) != len(tasks):
        return None
    
    return sorted_tasks

def critical_path(tasks: dict[str, tuple[int, list[str]]]) -> int | None:
    graph = defaultdict(list)
    in_degree = {task: 0 for task in tasks}
    
    for task, (duration, dependencies) in tasks.items():
        for dependency in dependencies:
            graph[dependency].append(task)
            in_degree[task] += 1
    
    queue = deque([task for task in tasks if in_degree[task] == 0])
    
    sorted_tasks = []
    
    while queue:
        task = queue.popleft()
        sorted_tasks.append(task)
        
        for neighbor in graph[task]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)
    
    if len(sorted_tasks) != len(tasks):
        return None
    
    max_duration = 0
    for task, (duration, _) in tasks.items():
        max_duration = max(max_duration, duration)
    
    return max_duration
