def plan_order(tasks: dict[str, tuple[int, list[str], int]], workers: int) -> list[str] | None:
    all_tasks = set(tasks.keys())
    started = []
    time = 0

    while True:
        ready = [
            t for t in all_tasks
            if t not in started
            and all(d == '' or d in started for d in tasks[t][1])
        ]
        if not ready:
            break

        ready.sort(key=lambda t: (-tasks[t][2], tasks[t][0], t))
        selected = ready[:workers]
        started.extend(selected)

        if selected:
            min_dur = min(tasks[t][0] for t in selected)
            time += min_dur

    return None if len(started) != len(all_tasks) else started


def critical_path(tasks: dict[str, tuple[int, list[str], int]]) -> int | None:
    visited = set()
    path = set()

    def dfs(node):
        if node in path:
            raise ValueError("cycle")
        if node in visited:
            return 0
        visited.add(node)
        path.add(node)

        max_len = tasks[node][0]
        for dep in tasks[node][1]:
            if dep == '':
                continue
            child_len, _ = dfs(dep)
            if child_len is None:
                raise ValueError("cycle")
            max_len += child_len

        path.remove(node)
        return max_len

    try:
        result = 0
        for node in tasks:
            if node not in visited:
                result = max(result, dfs(node))
        return result
    except ValueError:
        return None


def makespan(tasks: dict[str, tuple[int, list[str], int]], workers: int) -> int | None:
    all_tasks = set(tasks.keys())
    started = set()
    start_time = {}
    finish_time = {}
    time = 0
    max_finish = 0

    while True:
        ready = [
            t for t in all_tasks
            if t not in started
            and all(d == '' or d in started for d in tasks[t][1])
        ]
        if not ready:
            break

        ready.sort(key=lambda t: (-tasks[t][2], tasks[t][0], t))
        selected = ready[:workers]

        for t in selected:
            start_time[t] = time
            finish_time[t] = time + tasks[t][0]
            max_finish = max(max_finish, finish_time[t])

        started.update(selected)
        min_dur = min(tasks[t][0] for t in selected)
        time += min_dur

    if len(started) != len(all_tasks):
        return None
    return max_finish
