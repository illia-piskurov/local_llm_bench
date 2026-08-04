def topo_sort(tasks: dict[str, list[str]]) -> list[str] | None:
    in_degree = {task: 0 for task in tasks}
    for dependencies in tasks.values():
        for dep in dependencies:
            in_degree[dep] += 1

    queue = [task for task in tasks if in_degree[task] == 0]
    sorted_tasks = []
    
    while queue:
        current = queue.pop(0)
        sorted_tasks.append(current)
        
        for dependent in tasks.get(current, []):
            in_degree[dependent] -= 1
            if in_degree[dependent] == 0:
                queue.append(dependent)
    
    if len(sorted_tasks) != len(tasks):
        return None
    return sorted_tasks
