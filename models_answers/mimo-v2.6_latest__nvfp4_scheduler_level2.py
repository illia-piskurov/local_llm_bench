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


def critical_path(tasks: dict[str, tuple[int, list[str]]]) -> int | None:
    """Return the length of the critical path — the total duration of the
    longest dependent sequence of tasks — or None if the dependency graph
    contains a cycle."""
    if not tasks:
        return 0

    graph = {task: set(dependencies) for task, (duration, dependencies) in tasks.items()}
    visited: set[str] = set()
    path: set[str] = set()
    memo: dict[str, int] = {}

    def longest_path(task_name: str) -> int:
        if task_name not in graph:
            return 0

        if task_name in path:
            return -1

        if task_name in visited:
            return memo[task_name]

        path.add(task_name)
        longest = 0
        for dependency in graph[task_name]:
            longest = max(longest, longest_path(dependency))
        path.discard(task_name)
        visited.add(task_name)
        memo[task_name] = longest + tasks[task_name][0]
        return memo[task_name]

    for task_name in graph:
        longest_path(task_name)

    return max(memo.values())
