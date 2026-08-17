def topo_sort(tasks: dict[str, list[str]]) -> list[str] | None:
    # compute indegree for each task
    indeg = {t: 0 for t in tasks}
    for deps in tasks.values():
        for d in deps:
            if d in indeg:
                indeg[d] += 1

    # queue of tasks with no remaining dependencies
    zero_dep = [t for t, deg in indeg.items() if deg == 0]
    order: list[str] = []

    while zero_dep:
        v = zero_dep.pop(0)
        order.append(v)
        for nxt in tasks.get(v, []):
            indeg[nxt] -= 1
            if indeg[nxt] == 0:
                zero_dep.append(nxt)

    # if not all tasks were processed, there is a cycle
    return order if len(order) == len(tasks) else None
