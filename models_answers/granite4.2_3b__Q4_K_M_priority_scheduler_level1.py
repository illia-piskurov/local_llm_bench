def plan_order(tasks: dict[str, tuple[int, list[str], int]], workers: int) -> list[str] | None:
    # Build graph and reverse mapping
    graph = {name: [] for name in tasks}
    indeg = {name: 0 for name in tasks}
    rev = {name: [] for name in tasks}
    for name, (dur, deps, pri) in tasks.items():
        for dep in deps:
            graph[dep].append(name)
            indeg[name] += 1
            rev[name].append(dep)

    # Detect cycle using DFS
    visited = {name: 0 for name in tasks}
    stack = []
    def dfs(v):
        visited[v] = 1
        stack.append(v)
        for w in graph[v]:
            if visited[w] == 0:
                if dfs(w):
                    return True
            elif visited[w] == 1:
                return True
        visited[v] = 2
        stack.pop()
        return False
    for v in tasks:
        if visited[v] == 0 and dfs(v):
            return None

    # Topological order
    order = [v for v in tasks if visited[v] == 2]
    # Kahn's algorithm
    q = [v for v in tasks if indeg[v] == 0]
    while q:
        cur = q.pop(0)
        order.append(cur)
        for nxt in graph[cur]:
            indeg[nxt] -= 1
            if indeg[nxt] == 0:
                q.append(nxt)

    # Preprocess tasks: duration, deps, priority
    proc = {name: (tasks[name][0], tasks[name][1], tasks[name][2]) for name in tasks}

    # Simulation
    ready = []          # (priority, duration, name)
    in_prog = set()     # tasks currently running
    running = []        # (start_time, name)
    finished = []       # (completion_time, name)
    time = 0
    # initial ready tasks (deps satisfied)
    for name in tasks:
        dur, deps, pri = proc[name]
        if all(dep in tasks for dep in deps):
            ready.append((pri, dur, name))
    ready.sort(key=lambda x: (-x[0], x[1], x[2]))

    while ready or running:
        # Choose next task to start
        if not running:
            # pick ready task with highest priority, shortest duration, alphabetical
            ready.sort(key=lambda x: (-x[0], x[1], x[2]))
            if ready:
                pri, dur, name = ready[0]
                ready.remove(ready[0])
                start = time
                running.append((start, name))
                in_prog.add(name)
                # schedule completion
                finish = start + dur
                finished.append((finish, name))
                # add its dependents to ready when they become ready later
                # we will recompute ready after each step; simpler: just continue loop
        else:
            # advance time to next possible start
            # find earliest finish among running tasks
            earliest = min(running, key=lambda x: x[0])
            start = earliest[0]
            # tasks that finish at this time become ready
            for (r_start, r_name) in running:
                if r_start == start:
                    in_prog.remove(r_name)
                    # add its dependents
                    for dep in graph[r_name]:
                        if all(d in tasks for d in proc[dep][1]):
                            ready.append((proc[dep][2], proc[dep][0], dep))
                    # also the task itself becomes ready? it's already running
            # now pick next ready task according to rules
            ready.sort(key=lambda x: (-x[0], x[1], x[2]))
            if ready:
                pri, dur, name = ready[0]
                ready.remove(ready[0])
                running.append((start, name))
                in_prog.add(name)
                finish = start + dur
                finished.append((finish, name))
            else:
                # no ready task, advance time to next possible start of running tasks
                # find max start among running tasks
                max_start = max(r[0] for r in running)
                time = max_start
                continue

        # enforce worker limit
        if len(running) >= workers:
            # advance time to next running task finish
            next_finish = min(r[0] + proc[r[1]][0] for r in running)
            time = next_finish
            # update running tasks: those that finish exactly at time become ready
            new_running = []
            for (r_start, r_name) in running:
                if r_start + proc[r_name][0] == time:
                    in_prog.remove(r_name)
                    # add dependents
                    for dep in graph[r_name]:
                        if all(d in tasks for d in proc[dep][1]):
                            ready.append((proc[dep][2], proc[dep][0], dep))
                    # this task is now finished, record
                    finished.append((time, r_name))
                else:
                    new_running.append((r_start, r_name))
            running = new_running
            # re-sort ready later
        else:
            # we already advanced time appropriately; just continue loop
            pass

    # Return task names in order they finish (or start? we used finish)
    return [name for _, name in sorted(finished, key=lambda x: x[0])]
