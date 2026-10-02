def topo_sort(tasks: dict[str, list[str]]) -> list[str] | None:
    # Build adjacency list (task depends on dep)
    graph = {}  # task -> list of dependencies it depends on
    in_degree = {}  # count of incoming edges for each node
    
    for task, deps in tasks.items():
        if task not in graph:
            graph[task] = []
        for dep in deps:
            if dep not in graph:
                graph[dep] = []
            graph[task].append(dep)  # task depends on dep
    
    # Initialize in-degree counts (how many tasks depend on this one)
    for task in tasks:
        in_degree[task] = len(graph.get(task, []))
    
    visited = set()
    rec_stack = set()
    result = []
    
    def dfs(node):
        if node not in graph:  # Already processed or doesn't exist
            return
        
        visited.add(node)
        rec_stack.add(node)
        
        for dep in graph.get(node, []):
            if dep not in visited:
                continue
            
            if dep in rec_stack:
                return None  # Cycle detected!
            
            dfs(dep)
        
        result.append(node)
        rec_stack.remove(node)
    
    # Run DFS from each unvisited node to handle disconnected components
    for task in tasks:
        if task not in visited:
            dfs(task)
    
    return None if any(dfs_cycle) else result
