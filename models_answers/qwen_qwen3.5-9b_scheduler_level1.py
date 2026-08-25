import collections

def topo_sort(tasks: dict[str, list[str]]) -> list[str] | None:
    # Collect all unique task names from keys and values
    all_tasks = set(tasks.keys())
    for deps in tasks.values():
        all_tasks.update(deps)
    
    if not all_tasks:
        return []

    # Build adjacency list (dependency -> dependents) and calculate in-degrees
    graph = {task: [] for task in all_tasks}
    in_degree = {task: 0 for task in all_tasks}
    
    for task, dependencies in tasks.items():
        current_in_degree = len(dependencies)
        # Set in-degree based on the number of dependencies listed for this task
        in_degree[task] = current_in_degree
        
        for dep in dependencies:
            graph[dep].append(task)
            
    # Kahn's Algorithm
    queue = collections.deque([task for task in all_tasks if in_degree[task] == 0])
    result = []
    
    while queue:
        current_task = queue.popleft()
        result.append(current_task)
        
        for dependent in graph[current_task]:
            in_degree[dependent] -= 1
            if in_degree[dependent] == 0:
                queue.append(dependent)
                
    # Check for cycle: if not all tasks are visited, there is a cycle
    return result if len(result) == len(all_tasks) else None
