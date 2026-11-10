def topo_sort(tasks: dict[str, list[str]]) -> list[str] | None:
    """Return a topologically sorted list of task names, or None if the
    dependency graph contains a cycle."""
    if not tasks:
        return []

    graph = {task: set(dependencies) for task, dependencies in tasks.items()}
    visited: set[str] = set()
    path: set[str] = set()
    result: list[str] = []

    def visit(task_name: str) -> None:
        if task_name not in graph:
            return

        if task_name in path:
            path.discard(task_name)
            result.reverse()
            return

        if task_name in visited:
            return

        path.add(task_name)
        for dependency in graph[task_name]:
            visit(dependency)
        path.discard(task_name)
        visited.add(task_name)
        result.append(task_name)

    for task_name in graph:
        visit(task_name)

    return result
