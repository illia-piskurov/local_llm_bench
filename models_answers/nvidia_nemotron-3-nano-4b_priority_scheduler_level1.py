def plan_order(tasks: dict[str, tuple[int, list[str], int]], workers: int) -> list[str] | None:
    all_tasks = set(tasks.keys())
    started = []
    time = 0

    while True:
        # tasks that are not yet started and whose dependencies are satisfied
        ready = [
            t for t in all_tasks
            if t not in started
            and all(d == '' or d in started for d in tasks[t][1])
        ]
        if not ready:
            break

        # sort by priority (desc), duration (asc), name (asc)
        ready.sort(key=lambda t: (-tasks[t][2], tasks[t][0], t))

        selected = ready[:workers]
        started.extend(selected)

        if selected:
            min_dur = min(tasks[t][0] for t in selected)
            time += min_dur

    # if any task remains unstarted, there is a cycle
    return None if len(started) != len(all_tasks) else started
