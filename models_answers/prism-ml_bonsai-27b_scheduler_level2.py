def topo_sort(tasks: dict[str, list[str]]) -> list[str] | None:
    in_degree = {task: 0 for task in tasks}
    adj = {task: [] for task in tasks}
    
    for task, deps in tasks.items():
        for dep in deps:
            if dep not in tasks:
                return None
            adj[dep].append(task)
            in_degree[task] += 1
    
    queue = [t for t in tasks if in_degree[t] == 0]
    
    sorted_tasks = []
    
    while queue:
        current = queue.pop(0)
        sorted_tasks.append(current)
        
        for neighbor in adj[current]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)
    
    return sorted_tasks if len(sorted_tasks) == len(tasks) else None


def critical_path(tasks: dict[str, tuple[int, list[str]]]) -> int | None:
    # Проверяем наличие циклов с помощью topo_sort
    deps_only = {task: deps for task, (duration, deps) in tasks.items()}
    order = topo_sort(deps_only)
    
    if order is None:
        return None
    
    # Вычисляем longest path до каждой задачи в топологическом порядке
    earliest_start = {}
    
    for task in order:
        duration, deps = tasks[task]
        
        if not deps:
            earliest_start[task] = 0
        else:
            max_dep_end = max(earliest_start[dep] + tasks[dep][0] for dep in deps)
            earliest_start[task] = max_dep_end
    
    # Критический путь — максимальное время завершения всех задач
    if not earliest_start:
        return 0
    
    return max(earliest_start[task] + tasks[task][0] for task in earliest_start)
