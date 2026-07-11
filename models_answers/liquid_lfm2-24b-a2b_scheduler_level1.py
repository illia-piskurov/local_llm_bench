def topo_sort(tasks: dict[str, list[str]]) -> list[str] | None:
    from collections import deque

    # Собрать все задачи и их зависимости в одном графе
    all_nodes = set(tasks.keys())
    for deps in tasks.values():
        for d in deps:
            all_nodes.add(d)

    # Создать график и счётчик зависимостей для каждой задачи (индекс)
    graph = {node: [] for node in all_nodes}
    indegree = {node: 0 for node in all_nodes}

    for node, deps in tasks.items():
        for dep in deps:
            graph[dep].append(node)
            indegree[node] += 1

    # Начальные задачи (индекс 0 — те, у которых нет зависимостей)
    queue = deque([node for node in all_nodes if indegree[node] == 0])
    topo_order = []

    while queue:
        current = queue.popleft()
        topo_order.append(current)
        for neighbor in graph[current]:
            indegree[neighbor] -= 1
            if indegree[neighbor] == 0:
                queue.append(neighbor)

    # Если все задачи были обработаны — возвращаем отсортированный список
    if len(topo_order) == len(all_nodes):
        return topo_order
    else:
        # Если есть цикл, возвращаем None
        return None
