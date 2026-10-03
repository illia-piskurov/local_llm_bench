def topo_sort(tasks: dict[str, list[str]]) -> list[str] | None:
    visited = {}
    result = []

    def dfs(task):
        if task in visited:
            return visited[task]
        visited[task] = "visiting"
        for dep in tasks.get(task, []):
            if dfs(dep) == "cycle":
                return "cycle"
        visited[task] = "visited"
        result.append(task)
        return True

    for task in tasks:
        if dfs(task) == "cycle":
            return None
    return result
