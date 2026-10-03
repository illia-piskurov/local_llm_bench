from collections import defaultdict, deque

def critical_path(tasks: dict[str, tuple[int, list[str], int]]) -> int | None:
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
    longest_path_sum = 0
    task_times = {task: 0 for task in tasks}
    
    while sorted_tasks:
        ready_tasks = [task for task in sorted_tasks if all(dep_task not in task_times or task_times[dep_task] <= current_time for dep_task in tasks[task][1])]
        
        # Schedule new tasks based on priority, duration, and name
        ready_tasks.sort(key=lambda t: (-tasks[t][2], tasks[t][0], t))
        
        while workers > 0 and ready_tasks:
            task = ready_tasks.pop(0)
            start_time = current_time if all(dep_task not in task_times or task_times[dep_task] <= current_time for dep_task in tasks[task][1]) else max(task_times[dep_task] for dep_task in tasks[task][1])
            task_times[task] = start_time + tasks[task][0]
            longest_path_sum = max(longest_path_sum, task_times[task])
            sorted_tasks.remove(task)
            current_time += 1
        
        # Advance time
        if sorted_tasks:
            next_end_time = min(tasks[task][0] for task in sorted_tasks if all(dep_task not in task_times or task_times[dep_task] <= current_time for dep_task in tasks[task][1]))
            current_time += next_end_time
    
    return longest_path_sum

def makespan(tasks: dict[str, tuple[int, list[str], int]], workers: int) -> int | None:
    sorted_tasks = []
    
    while tasks:
        ready_tasks = [task for task in tasks if all(dep_task not in [t[0] for t in sorted_tasks] or tasks[t[0]][2] <= tasks[task][2] and tasks[t[0]][0] <= tasks[task][0] and tasks[t[0]][1] <= tasks[task][1] else False for dep_task in tasks[task])]
        
        # Schedule new tasks based on priority, duration, and name
        ready_tasks.sort(key=lambda t: (-tasks[t][2], tasks[t][0], t))
        
        while workers > 0 and ready_tasks:
            task = ready_tasks.pop(0)
            sorted_tasks.append((task, current_time := max(tasks[dep_task][0] for dep_task in tasks[task][1]) if tasks[task][1] else 0 + tasks[task][0]))
            tasks.pop(task)
            workers -= 1
    
    return max(end_time for _, end_time in sorted_tasks) if not any(dep_task in [t[0] for t in sorted_tasks] or tasks[dep_task][2] <= tasks[task][2] and tasks[dep_task][0] <= tasks[task][0] and tasks[dep_task][1] <= tasks[task][1] else True for task, end_time in sorted_tasks for dep_task in tasks[task][1])
