def critical_path(tasks: dict[str, tuple[int, list[str]]]) -> int | None:
    def dfs(task):
        if memo[task] is not None:
            return memo[task]
        max_duration = 0
        for dep in tasks.get(task, []):
            duration = dfs(dep)
            if duration is None:
                return None  # cycle detected
            max_duration = max(max_duration, duration)
        memo[task] = max_duration + tasks[task][0]
        return memo[task]

    memo = {task: None for task in tasks}
    result = None

    for task in tasks:
        duration = dfs(task)
        if duration is None:
            return None  # cycle detected
        if result is None or duration > result:
            result = duration

    return result
