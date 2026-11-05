def topo_sort(tasks: dict[str, list[str]]) -> list[str] | None:
    graph = {name: set(deps) for name, deps in tasks.items()}
    parent_nodes = {name: None for name in tasks.keys()}
    visited = set()
    sorted_tasks = []

    def dfs(node: str) -> None:
        visited.add(node)
        for neighbor in graph[node]:
            if neighbor not in visited:
                dfs(neighbor)
        sorted_tasks.append(node)

    for node in graph:
        if node not in visited:
            dfs(node)

    if any(node is not None for node in visited):
        return None

    return sorted_tasks

def critical_path(tasks: dict[str, tuple[int, list[str]]]) -> int | None:
    graph = {name: (duration, deps) for name, (duration, deps) in tasks.items()}
    sorted_tasks = topo_sort(graph)

    if sorted_tasks is None:
        return None

    critical_paths = {}
    for task in sorted_tasks:
        path = [task]
        while parent_nodes[task] is not None:
            task = parent_nodes[task]
            path.insert(0, task)
        critical_paths[task] = len(path)

    longest_path = max(critical_paths.values())
    return longest_path
