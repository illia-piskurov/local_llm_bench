def topo_sort(tasks: dict[str, list[str]]) -> list[str] | None:
    if not tasks:
        return []
    graph = {task: [] for task in tasks}
    for dep, sub_tasks in tasks.items():
        for sub_task in sub_tasks:
            graph[dep].append(sub_task)

    visited = set()
    order = []

    def dfs(node):
        if node in visited:
            return
        visited.add(node)
        for child in graph[node]:
            dfs(child)
        order.append(node)

    for task in tasks:
        if task not in visited:
            dfs(task)

    return order[::-1]
