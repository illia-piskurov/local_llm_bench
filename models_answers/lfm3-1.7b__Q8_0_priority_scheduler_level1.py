def plan_order(tasks: dict[str, tuple[int, list[str], int]], workers: int):
    # Build info for each task
    info = {}
    for name, (dur, deps, prio) in tasks.items():
        info[name] = {'duration': dur, 'deps': set(deps), 'priority': prio}
    
    # Cycle detection via DFS on graph where edges from task to its dependencies.
    graph = {name: list(info[name]['deps']) for name in info}  # each node -> deps
    visited = set()
    rec_stack = set()

    def dfs(node):
        if node not in visited:
            visited.add(node)
            rec_stack.add(node)
            for neighbor in graph.get(node, []):  # dependency is neighbor? Actually edge from node to dep.
                if neighbor not in visited:
                    if dfs(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True
            rec_stack.remove(node)
        return False

    cycle = False
    for node in info:
        if node not in visited:
            if dfs(node):
                cycle = True
                break
    if cycle:
        return None
    
    # Build dependents reverse graph
    dependents = {name: [] for name in info}  # list of tasks that depend on this task
    for name, data in info.items():
        deps_set = set(data['deps'])
        for dep in deps_set:
            if dep in dependents:
                dependents[dep].append(name)
    
    # priority queue for ready nodes: (-priority, duration, name)
    import heapq
    heap = []
    remaining_prereq = {name: len(info[name]['deps']) for name in info}
    for name, data in info.items():
        if remaining_prereq[name] == 0:
            # push tuple: (-prio, duration, name)
            heapq.heappush(heap, (-data['priority'], data['duration'], name))
    
    result = []
    while heap:
        neg_pri, dur, name = heapq.heappop(heap)
        # Ensure it's not already in result (maybe duplicate due to multiple pushes?) We'll just use result append.
        result.append(name)
        # Update remaining prerequisites for dependents
        for dependent in dependents[name]:
            remaining_prereq[dependent] -= 1
            if remaining_prereq[dependent] == 0 and dependent not in result:
                heapq.heappush(heap, (-info[dependent]['priority'], info[dependent]['duration'], dependent))
    
    return result
