from collections import defaultdict, deque
import heapq

def critical_path(tasks: dict[str, tuple[int, list[str], int]]) -> int | None:
    # Check for cyclic dependencies using Kahn's algorithm
    in_degree = {task: 0 for task in tasks}
    graph = defaultdict(list)
    
    for task, (duration, deps, priority) in tasks.items():
        for dep in deps:
            if dep not in tasks:
                return None  # Dependency does not exist
            graph[dep].append(task)
            in_degree[task] += 1
    
    zero_in_degree = [task for task in in_degree if in_degree[task] == 0]
    
    if len(zero_in_degree) != len(tasks):
        return None  # Cyclic dependency detected
    
    # Calculate longest path
    dist = {task: 0 for task in tasks}
    pq = []
    for task in zero_in_degree:
        heapq.heappush(pq, (0, -tasks[task][0], task))
    
    while pq:
        _, duration, task = heapq.heappop(pq)
        for next_task in graph[task]:
            new_dist = dist[task] + tasks[next_task][0]
            if new_dist > dist[next_task]:
                dist[next_task] = new_dist
                heapq.heappush(pq, (new_dist, -tasks[next_task][0], next_task))
    
    return max(dist.values()) if len(tasks) == len(zero_in_degree) else None

def makespan(tasks: dict[str, tuple[int, list[str], int]], workers: int) -> int | None:
    # Check for cyclic dependencies using Kahn's algorithm
    in_degree = {task: 0 for task in tasks}
    graph = defaultdict(list)
    
    for task, (duration, deps, priority) in tasks.items():
        for dep in deps:
            if dep not in tasks:
                return None  # Dependency does not exist
            graph[dep].append(task)
            in_degree[task] += 1
    
    zero_in_degree = [task for task in in_degree if in_degree[task] == 0]
    
    if len(zero_in_degree) != len(tasks):
        return None  # Cyclic dependency detected
    
    # Priority queue to manage tasks by priority, duration, and name
    pq = []
    for task in zero_in_degree:
        _, deps, priority = tasks[task]
        heapq.heappush(pq, (-priority, -tasks[task][0], task))
    
    order = []
    current_time = 0
    running_tasks = defaultdict(int)
    
    while pq or any(running_tasks.values()):
        # Start new tasks if possible
        while len(running_tasks) < workers and pq:
            _, duration, task = heapq.heappop(pq)
            running_tasks[task] += -duration
        
        # Find the next time a task will finish
        min_finish_time = float('inf')
        for task, remaining in running_tasks.items():
            if remaining > 0:
                min_finish_time = min(min_finish_time, current_time + tasks[task][0])
        
        # Advance time to the minimum finish time
        current_time = min_finish_time
        
        # Complete tasks that finish at this time
        for task in list(running_tasks.keys()):
            if running_tasks[task] <= 0:
                order.append(task)
                del running_tasks[task]
                for next_task in graph[task]:
                    in_degree[next_task] -= 1
                    if in_degree[next_task] == 0:
                        _, deps, priority = tasks[next_task]
                        heapq.heappush(pq, (-priority, -tasks[next_task][0], next_task))
        
        # Decrease remaining time for running tasks
        for task in running_tasks:
            running_tasks[task] -= 1
    
    return current_time if len(order) == len(tasks) else None
