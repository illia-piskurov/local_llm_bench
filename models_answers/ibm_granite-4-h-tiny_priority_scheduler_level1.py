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
        order = []
        
        while queue:
            current = min(queue, key=lambda t: (-tasks[t][2], tasks[t][0], t))
            queue.remove(current)
            order.append(current)
            
            for neighbor in graph[current]:
                indegree[neighbor] -= 1
                if indegree[neighbor] == 0:
                    queue.append(neighbor)
        
        return order if len(order) == len(tasks) else None
    
    sorted_tasks = topological_sort()
    
    if sorted_tasks is None:
        return None
    
    current_time = 0
    running_tasks = []
    result = []
    
    while sorted_tasks or running_tasks:
        ready_tasks = [task for task in sorted_tasks if all(dep_task not in running_tasks for dep_task in tasks[task][1])]
        
        # Schedule new tasks based on priority, duration, and name
        ready_tasks.sort(key=lambda t: (-tasks[t][2], tasks[t][0], t))
        
        while workers > 0 and ready_tasks:
            task = ready_tasks.pop(0)
            running_tasks.append(task)
            sorted_tasks.remove(task)
            result.append((task, current_time))
            workers -= 1
        
        # Advance time
        if running_tasks:
            next_end_time = min(tasks[task][0] for task in running_tasks)
            current_time += next_end_time
            for i, (task, start_time) in enumerate(result):
                if tasks[task][0] == next_end_time and task in running_tasks:
                    result[i] = (task, current_time)
                    running_tasks.remove(task)
                    workers += 1
    
    return [task for task, _ in sorted(result, key=lambda x: x[1])]
