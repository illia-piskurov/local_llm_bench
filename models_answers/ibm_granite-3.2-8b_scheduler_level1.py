def topo_sort(tasks: dict[str, list[str]]) -> list[str] | None:
    from collections import defaultdict

    def dfs(node, visited, stack, graph):
        if node in visited:
            return False  # Cycle detected

        visited.add(node)
        for neighbor in graph[node]:
            if not dfs(neighbor, visited, stack, graph):
                return False

        stack.append(node)
        return True

    graph = defaultdict(list)
    for task, dependencies in tasks.items():
        for dep in dependencies:
            graph[dep].append(task)

    visited = set()
    stack = []

    for node in tasks:
        if not dfs(node, visited, stack, graph):
            return None  # Cycle detected

    return stack[::-1]
