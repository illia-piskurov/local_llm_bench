from collections import defaultdict, deque

def plan_order(tasks: dict[str, tuple[int, list[str], int]], workers: int) -> list[str] | None:
    # Build graph and indegree map for cycle detection
    graph = defaultdict(list)
    indegree = {task: 0 for task in tasks}
    
    for task, (_, deps, _) in tasks.items():
        for dep in deps:
            graph[dep].append(task)
            indegree[task] += 1
            
    # Detect cycles
    if any(indegree.values()) or len(graph) != len(tasks):
        return None
    
    # Prepare ready queue with initially available tasks (no dependencies)
    ready = []
    for task, (_, deps, _) in tasks.items():
        if not indegree[task]:
            ready.append(task)
    
    ready.sort(key=lambda t: (-tasks[t][2], tasks[t][0], t))
    
    schedule = []
    current_time = 0
    running_tasks = {}
    
    while ready or running_tasks:
        # Add newly available tasks to the ready queue
        while ready and len(running_tasks) < workers:
            task = ready.pop(0)
            start_time = current_time + tasks[task][0]
            schedule.append((start_time, task))
            running_tasks[start_time] = task
            # Check if any currently running tasks can finish this time unit
            finished_this_step = []
            for st, t in list(running_tasks.items()):
                if st + tasks[t][0] == current_time:
                    finished_this_step.append(t)
            for t in finished_this_step:
                del running_tasks[t]
        
        # If no more tasks can be scheduled now and there are still running ones,
        # advance time to the next task completion
        if not ready and running_tasks:
            min_start = min(st for st in running_tasks.keys())
            current_time = min_start
        
        # Prepare for next iteration
        current_time += 1
    
    return [task for _, task in schedule]
