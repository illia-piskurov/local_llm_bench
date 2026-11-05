def critical_path(tasks: dict[str, tuple[int, list[str]]]) -> int | None:
    def topo_sort_duration(tasks: dict[str, tuple[int, list[str]]]) -> dict[str, int]:
        in_degree = {task: 0 for task, _ in tasks.items()}
        for task, (duration, deps) in tasks.items():
            for dep in deps:
                in_degree[dep] += 1

        queue = [task for task in in_degree if in_degree[task] == 0]
        earliest_start = {task: 0 for task in tasks}
        earliest_start.update({task: float('inf') for task in tasks if task not in queue})

        while queue:
            task = queue.pop(0)
            for dep in tasks[task][1]:
                in_degree[dep] -= 1
                if in_degree[dep] == 0:
                    queue.append(dep)
                earliest_start[dep] = max(earliest_start[dep], earliest_start[task] + tasks[task][0])

        return earliest_start

    earliest_start = topo_sort_duration(tasks)
    if any(task not in earliest_start for task in tasks):
        return None

    max_duration = max(earliest_start[task] + tasks[task][0] for task in tasks)
    return max_duration
