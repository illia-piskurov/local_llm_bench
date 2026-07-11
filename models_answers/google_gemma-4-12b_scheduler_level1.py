def topo_sort(tasks: dict[str, list[str]]) -> list[str] | None:
    # Identify all unique tasks in the system (both keys and items in dependency lists)
    all_nodes = set(tasks.keys())
    for deps in tasks.values():
        all_nodes.update(deps)

    # Build an adjacency list where adj[u] contains tasks that depend on u
    # And calculate the in-degree (number of dependencies) for each task
    adj = {node: [] for node in all_nodes}
    in_degree = {node: 0 for node in all_nodes}

    for task, deps in tasks.items():
        # The number of items in 'deps' is the count of requirements for 'task'
        in_degree[task] = len(deps)
        for d in deps:
            # If 'task' depends on 'd', then there is a directed edge from 'd' to 'task'
            adj[d].append(task)

    # Kahn's algorithm for topological sorting
    # Start with all tasks that have no dependencies
    queue = [node for node in all_nodes if in_degree[node] == 0]
    result = []

    # Process the queue (using a pointer to simulate O(1) pop from front)
    head = 0
    while head < len(queue):
        u = queue[head]
        head += 1
        result.append(u)
        
        for v in adj[u]:
            in_degree[v] -= 1
            if in_degree[v] == 0:
                queue.append(v)

    # If the result length matches the total number of unique tasks, no cycle exists
    if len(result) == len(all_nodes):
        return result
    else:
        # A cycle was detected (some nodes never reached in-degree 0)
        return None
