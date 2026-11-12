def topo_sort(tasks: dict[str, list[str]]) -> list[str] | None:
    from collections import deque

    in_degree = {task: 0 for task in tasks}
    for deps in tasks.values():
        for dep in deps:
            in_degree[dep] += 1

    queue = deque([task for task in in_degree if in_degree[task] == 0])
    sorted_order = []

    while queue:
        task = queue.popleft()
        sorted_order.append(task)

        for dep in tasks[task]:
            in_degree[dep] -= 1
            if in_degree[dep] == 0:
                queue.append(dep)

    if len(sorted_order) != len(tasks):
        return None

    return sorted_order
