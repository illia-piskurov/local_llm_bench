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

def critical_path(tasks: dict[str, tuple[int, list[str]]]) -> int | None:
    # Collect all unique task names from keys and values
    all_tasks = set(tasks.keys())
    for _, deps in tasks.values():
        all_tasks.update(deps)
    
    if not all_tasks:
        return 0

    # Build adjacency list (dependency -> dependents) and calculate in-degrees
    graph = {task: [] for task in all_tasks}
    in_degree = {task: 0 for task in all_tasks}
    
    for task, (duration, dependencies) in tasks.items():
        current_in_degree = len(dependencies)
        in_degree[task] = current_in_degree
        
        for dep in dependencies:
            graph[dep].append(task)
            
    # Kahn's Algorithm to check for cycle and get topological order
    queue = collections.deque([task for task in all_tasks if in_degree[task] == 0])
    topo_order = []
    
    while queue:
        current_task = queue.popleft()
        topo_order.append(current_task)
        
        for dependent in graph[current_task]:
            in_degree[dependent] -= 1
            if in_degree[dependent] == 0:
                queue.append(dependent)
    
    # If not all tasks are visited, there is a cycle
    if len(topo_order) != len(all_tasks):
        return None
    
    # Calculate earliest completion time for each task using topological order
    earliest_completion = {task: 0 for task in all_tasks}
    
    for task in topo_order:
        duration, _ = tasks[task]
        max_dep_completion = 0
        
        _, dependencies = tasks[task]
        for dep in dependencies:
            if dep in earliest_completion:
                max_dep_completion = max(max_dep_completion, earliest_completion[dep])
        
        earliest_completion[task] = max_dep_completion + duration
    
    # Critical path length is the maximum earliest completion time among all tasks
    return max(earliest_completion.values()) if earliest_completion else 0
