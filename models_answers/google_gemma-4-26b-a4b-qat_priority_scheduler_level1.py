def plan_order(tasks: dict[str, tuple[int, list[str], int]], workers: int) -> list[str] | None:
    # 1. Cycle Detection using Kahn's Algorithm
    in_degree_cycle = {name: len(deps) for name, (dur, deps, prio) in tasks.items()}
    adj = {name: [] for name in tasks}
    for name, (dur, deps, prio) in tasks.items():
        for d in deps:
            adj[d].append(name)

    queue = [n for n in tasks if in_degree_cycle[n] == 0]
    visited_count = 0
    while queue:
        u = queue.pop(0)
        visited_count += 1
        for v in adj[u]:
            in_degree_cycle[v] -= 1
            if in_degree_cycle[v] == 0:
                queue.append(v)
    
    if visited_count < len(tasks):
        return None

    # 2. Simulation
    current_time = 0
    completed = set()
    started = []
    running = []  # List of (finish_time, name)
    in_degree = {name: len(deps) for name, (dur, deps, prio) in tasks.items()}
    
    # Tasks that have no dependencies and are ready to be picked up
    ready_to_start = [n for n in tasks if in_degree[n] == 0]
    # Tasks that have been started but not yet finished
    started_set = set()

    while len(completed) < len(tasks):
        # A. Complete tasks that finish at the current time
        # We must find all tasks finishing at current_time to update dependencies
        finished_this_step = []
        new_running = []
        for finish_time, name in running:
            if finish_time == current_time:
                finished_this_step.append(name)
            else:
                new_running.append((finish_time, name))
        running = new_running

        for name in finished_this_step:
            completed.add(name)
            for neighbor in adj[name]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    ready_to_start.append(neighbor)

        # B. Start new tasks
        # Sort ready tasks by: priority (desc), duration (asc), name (asc)
        ready_to_start.sort(key=lambda x: (-tasks[x][2], tasks[x][0], x))
        
        while len(running) < workers and ready_to_start:
            name = ready_to_start.pop(0)
            duration = tasks[name][0]
            running.append((current_time + duration, name))
            started.append(name)
            started_set.add(name)

        # C. Advance time
        if running:
            # Jump to the next time a task finishes
            next_event_time = min(f_time for f_time, name in running)
            current_time = next_event_time
        elif len(completed) < len(tasks):
            # If no tasks are running and we haven't finished all tasks, 
            # but no tasks are ready, it's a logic error or cycle (already checked)
            break

    return started
