def plan_order(tasks: dict[str, tuple[int, list[str], int]], workers: int) -> list[str] | None:
    """
    Планирует выполнение задач с зависимостями, приоритетами и ограниченным числом исполнителей.

    Args:
        tasks (dict[str, tuple[int, list[str], int]]): Словарь, где ключ - имя задачи, а значение - кортеж (duration, deps, priority).
        workers (int): Количество доступных исполнителей.

    Returns:
        list[str] | None: Список имен задач в порядке выполнения или None, если есть цикл зависимостей.
    """

    in_degree = {}
    graph = {}
    for task, (duration, deps, _) in tasks.items():
        in_degree[task] = len(deps)
        graph[task] = []

    for task, (duration, deps, _) in tasks.items():
        for dep in deps:
            graph[dep].append(task)

    queue = [task for task in tasks if in_degree[task] == 0]
    if not queue:
        return []  # No tasks to execute

    scheduled_tasks = []
    running_tasks = []
    current_time = 0

    while queue or running_tasks:
        # Sort ready tasks based on priority, duration, and name
        ready_tasks = []
        for task in queue:
            if all(dep in scheduled_tasks for dep in tasks[task][1]):
                ready_tasks.append(task)

        ready_tasks.sort(key=lambda x: (-tasks[x][2], tasks[x][0], x))  # Higher priority, shorter duration, ascending name

        available_workers = workers - len(running_tasks)
        tasks_to_start = []

        for task in ready_tasks:
            if available_workers > 0:
                tasks_to_start.append(task)
                available_workers -= 1

        if tasks_to_start:
            for task in tasks_to_start:
                scheduled_tasks.append(task)
                running_tasks.append(task)
                queue.remove(task)

        # Advance time for running tasks
        completed_tasks = []
        for task in running_tasks:
            duration, _, _ = tasks[task]
            current_time += duration
            if current_time > duration:  # Check if the task is completed
                completed_tasks.append(task)

        running_tasks = [task for task in running_tasks if task not in completed_tasks]

        for task in completed_tasks:
            for neighbor in graph[task]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0 and neighbor not in scheduled_tasks:
                    queue.append(neighbor)


    if len(scheduled_tasks) != len(tasks):
        return None  # Cycle detected

    return scheduled_tasks


def critical_path(tasks: dict[str, tuple[int, list[str], int]]) -> int | None:
    """
    Вычисляет длину самого длинного зависимого пути в задаче.

    Args:
        tasks (dict[str, tuple[int, list[str], int]]): Словарь задач с длительностью, зависимостями и приоритетом.

    Returns:
        int | None: Длина самого длинного зависимого пути или None, если есть цикл зависимостей.
    """
    in_degree = {}
    graph = {}
    for task, (duration, deps, _) in tasks.items():
        in_degree[task] = len(deps)
        graph[task] = []

    for task, (duration, deps, _) in tasks.items():
        for dep in deps:
            graph[dep].append(task)

    queue = [task for task in tasks if in_degree[task] == 0]
    if not queue:
        return 0  # No tasks to execute

    dp = {}  # Store the longest path length starting from each task

    while queue:
        task = queue.pop(0)
        dp[task] = tasks[task][0]  # Initialize with the task's duration

        for neighbor in graph[task]:
            dp[neighbor] = max(dp[neighbor], dp[task] + tasks[neighbor][0])

            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    # Check for cycles (if not all tasks are reachable from the starting nodes)
    if len(dp) != len(tasks):
        return None  # Cycle detected

    return max(dp.values()) if dp else 0


def makespan(tasks: dict[str, tuple[int, list[str], int]], workers: int) -> int | None:
    """
    Вычисляет общее время завершения всех задач при заданных ограничениях.

    Args:
        tasks (dict[str, tuple[int, list[str], int]]): Словарь задач с длительностью, зависимостями и приоритетом.
        workers (int): Количество доступных исполнителей.

    Returns:
        int | None: Общее время завершения всех задач или None, если есть цикл зависимостей.
    """
    in_degree = {}
    graph = {}
    for task, (duration, deps, _) in tasks.items():
        in_degree[task] = len(deps)
        graph[task] = []

    for task, (duration, deps, _) in tasks.items():
        for dep in deps:
            graph[dep].append(task)

    queue = [task for task in tasks if in_degree[task] == 0]
    if not queue:
        return 0  # No tasks to execute

    scheduled_tasks = []
    running_tasks = []
    current_time = 0

    while queue or running_tasks:
        # Sort ready tasks based on priority, duration, and name
        ready_tasks = []
        for task in queue:
            if all(dep in scheduled_tasks for dep in tasks[task][1]):
                ready_tasks.append(task)

        ready_tasks.sort(key=lambda x: (-tasks[x][2], tasks[x][0], x))  # Higher priority, shorter duration, ascending name

        available_workers = workers - len(running_tasks)
        tasks_to_start = []

        for task in ready_tasks:
            if available_workers > 0:
                tasks_to_start.append(task)
                available_workers -= 1

        if tasks_to_start:
            for task in tasks_to_start:
                scheduled_tasks.append(task)
                running_tasks.append(task)
                queue.remove(task)

        # Advance time for running tasks
        completed_tasks = []
        for task in running_tasks:
            duration, _, _ = tasks[task]
            current_time += duration
            if current_time > duration:  # Check if the task is completed
                completed_tasks.append(task)

        running_tasks = [task for task in running_tasks if task not in completed_tasks]

        for task in completed_tasks:
            for neighbor in graph[task]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0 and neighbor not in scheduled_tasks:
                    queue.append(neighbor)


    if len(scheduled_tasks) != len(tasks):
        return None  # Cycle detected

    return current_time
