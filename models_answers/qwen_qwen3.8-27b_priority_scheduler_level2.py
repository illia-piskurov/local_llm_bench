from collections import deque


def _detect_cycle(tasks: dict[str, tuple[int, list[str], int]]) -> bool:
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {name: WHITE for name in tasks}

    def dfs(node: str) -> bool:
        color[node] = GRAY
        for dep in tasks[node][1]:
            if color[dep] == GRAY:
                return True
            if color[dep] == WHITE and dfs(dep):
                return True
        color[node] = BLACK
        return False

    for name in tasks:
        if color[name] == WHITE:
            if dfs(name):
                return True
    return False


def _build_dependents(tasks: dict[str, tuple[int, list[str], int]]) -> dict[str, list[str]]:
    dependents: dict[str, list[str]] = {name: [] for name in tasks}
    for name, (_, deps, _) in tasks.items():
        for dep in deps:
            dependents[dep].append(name)
    return dependents


def _simulate(tasks: dict[str, tuple[int, list[str], int]], workers: int) -> list[tuple[int, str]] | None:
    """Returns list of (start_time, task_name) in launch order, or None on cycle."""
    if _detect_cycle(tasks):
        return None

    dependents = _build_dependents(tasks)
    completed: set[str] = set()
    running: list[tuple[int, str]] = []
    ready: set[str] = {name for name, (_, deps, _) in tasks.items() if not deps}
    launches: list[tuple[int, str]] = []
    time = 0

    while len(completed) < len(tasks):
        still_running: list[tuple[int, str]] = []
        for end_time, tname in running:
            if end_time <= time:
                completed.add(tname)
                for dep_name in dependents[tname]:
                    if all(d in completed for d in tasks[dep_name][1]):
                        ready.add(dep_name)
            else:
                still_running.append((end_time, tname))
        running = still_running

        while len(running) < workers and ready:
            best = min(ready, key=lambda n: (-tasks[n][2], tasks[n][0], n))
            ready.remove(best)
            running.append((time + tasks[best][0], best))
            launches.append((time, best))

        if len(completed) >= len(tasks):
            break
        if not running:
            break

        time = min(end_time for end_time, _ in running)

    return launches


def plan_order(tasks: dict[str, tuple[int, list[str], int]], workers: int) -> list[str] | None:
    launches = _simulate(tasks, workers)
    if launches is None:
        return None
    return [name for _, name in launches]


def critical_path(tasks: dict[str, tuple[int, list[str], int]]) -> int | None:
    if not tasks:
        return 0
    if _detect_cycle(tasks):
        return None

    in_degree = {name: len(deps) for name, (_, deps, _) in tasks.items()}
    dependents = _build_dependents(tasks)

    queue = deque(name for name, deg in in_degree.items() if deg == 0)
    dist: dict[str, int] = {}

    while queue:
        node = queue.popleft()
        best_dep = max((dist[d] for d in tasks[node][1]), default=0)
        dist[node] = tasks[node][0] + best_dep
        for dep_name in dependents[node]:
            in_degree[dep_name] -= 1
            if in_degree[dep_name] == 0:
                queue.append(dep_name)

    return max(dist.values())


def makespan(tasks: dict[str, tuple[int, list[str], int]], workers: int) -> int | None:
    if not tasks:
        return 0
    if _detect_cycle(tasks):
        return None

    dependents = _build_dependents(tasks)
    completed: set[str] = set()
    running: list[tuple[int, str]] = []
    ready: set[str] = {name for name, (_, deps, _) in tasks.items() if not deps}
    time = 0
    max_end = 0

    while len(completed) < len(tasks):
        still_running: list[tuple[int, str]] = []
        for end_time, tname in running:
            if end_time <= time:
                completed.add(tname)
                if end_time > max_end:
                    max_end = end_time
                for dep_name in dependents[tname]:
                    if all(d in completed for d in tasks[dep_name][1]):
                        ready.add(dep_name)
            else:
                still_running.append((end_time, tname))
        running = still_running

        while len(running) < workers and ready:
            best = min(ready, key=lambda n: (-tasks[n][2], tasks[n][0], n))
            ready.remove(best)
            running.append((time + tasks[best][0], best))

        if len(completed) >= len(tasks):
            break
        if not running:
            break

        time = min(end_time for end_time, _ in running)

    return max_end
