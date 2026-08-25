def plan_order(tasks: dict[str, tuple[int, list[str], int]], workers: int) -> list[str] | None:
    # 1. Cycle Detection
    def has_cycle():
        visited = set()
        rec_stack = set()
        
        def dfs(node):
            if node in rec_stack:
                return True
            if node in visited:
                return False
            visited.add(node)
            rec_stack.add(node)
            
            # Get dependencies. If task not in tasks (shouldn't happen), deps is empty.
            for dep in tasks.get(node, ())[1]:
                if dfs(dep):
                    return True
            rec_stack.remove(node)
            return False

        for node in tasks:
            if dfs(node):
                return True
        return False

    if has_cycle():
        return None

    # 2. State Initialization
    # We create a copy of tasks to manage state (remaining time, active status)
    task_info = {}
    ready = set()
    finished = set()
    result = []
    active_count = 0

    for name, (duration, deps, priority) in tasks.items():
        task_info[name] = {
            'duration': duration,
            'priority': priority,
            'deps': deps,
            'remaining': duration,
            'active': False,
            'finished': False
        }
        # Tasks with no dependencies are ready to start immediately
        if not deps:
            ready.add(name)

    # 3. Simulation Loop
    # We loop until all tasks are finished
    while True:
        # Check for finished tasks
        for name in list(task_info.keys()):
            if task_info[name]['active'] and task_info[name]['remaining'] == 0:
                task_info[name]['active'] = False
                active_count -= 1
                task_info[name]['finished'] = True
                finished.add(name)
                
                # Update ready status for dependents
                for dep in task_info[name]['deps']:
                    if dep not in finished:
                        ready.add(dep)

        # Check if we can start new tasks
        if active_count < workers and ready:
            # Sort ready tasks: higher priority first, then lower duration, then name ascending
            sorted_ready = sorted(
                ready, 
                key=lambda x: (-task_info[x]['priority'], task_info[x]['duration'], x)
            )
            
            # Select tasks to start
            tasks_to_start = sorted_ready[:workers]
            
            for name in tasks_to_start:
                task_info[name]['active'] = True
                task_info[name]['remaining'] -= 1
                active_count += 1
                result.append(name)
                ready.remove(name)

        # Termination condition
        if active_count == 0 and not ready:
            break

    return result
