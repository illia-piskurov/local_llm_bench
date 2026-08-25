from collections import deque

def has_cycle(task, tasks: dict[str, tuple[int, list[str], int]], visited=None, recursion_stack=None):
    if visited is None:
        visited = set()
    if recursion_stack is None:
        recursion_stack = set()

    if task in recursion_stack:
        return True
    if task in visited:
        return False

    visited.add(task)
    recursion_stack.add(task)

    for dep in tasks.get(task, (0, [], 0))[1]:
        if has_cycle(dep, tasks, visited, recursion_stack):
            return True

    recursion_stack.remove(task)
    return False

def critical_path(tasks: dict[str, tuple[int, list[str], int]]) -> int | None:
    # Проверка на циклы
    for task in tasks:
        if has_cycle(task, tasks):
            return None

    # Нахождение самого длинного пути (критического пути)
    max_duration = 0
    stack = [(task, 0) for task in tasks]

    while stack:
        current_task, duration = stack.pop()
        current_duration = duration + tasks[current_task][0]
        if current_duration > max_duration:
            max_duration = current_duration

        # Добавляем зависимые задачи в стек для обработки
        for dep in reversed(tasks[current_task][1]):
            if dep not in visited:
                stack.append((dep, duration))

    return max_duration

def makespan(tasks: dict[str, tuple[int, list[str], int]], workers: int) -> int | None:
    # Проверка на циклы
    for task in tasks:
        if has_cycle(task, tasks):
            return None

    sorted_tasks = sorted(tasks.keys(), key=lambda x: (-tasks[x][2], tasks[x][0], x))
    ready_queue = deque()
    task_duration = {task: duration for task, (duration, _, _) in tasks.items()}
    available_workers = workers
    active_tasks = set()
    result = []
    current_time = 0

    while True:
        # Определяем задачи, готовые к выполнению в текущий момент времени
        new_ready = False
        for task in sorted_tasks:
            if all(dep not in active_tasks and dep != task for dep in tasks[task][1]):
                ready_queue.append(task)
                new_ready = True

        # Если ни одна задача не готова к выполнению, ждем следующего цикла
        if not new_ready and not ready_queue:
            continue

        # Выполняем задачи по правилам
        while available_workers > 0 and ready_queue:
            current_task = ready_queue.popleft()
            active_tasks.add(current_task)
            result.append((current_time, current_task))
            current_time += task_duration[current_task]
            available_workers -= 1

        # Проверка на завершение всех задач
        if len(result) != sum(1 for _ in tasks.values()):
            return None

    # Возвращаем общее время выполнения (маakespan)
    return current_time

def plan_order(tasks: dict[str, tuple[int, list[str], int]], workers: int) -> list[str] | None:
    if has_cycle(list(tasks.keys()), tasks):
        return None

    sorted_tasks = sorted(tasks.keys(), key=lambda x: (-tasks[x][2], tasks[x][0], x))
    ready_queue = deque()
    task_duration = {task: duration for task, (duration, _, _) in tasks.items()}
    available_workers = workers
    active_tasks = set()
    result = []
    current_time = 0

    while True:
        # Определяем задачи, готовые к выполнению в текущий момент времени
        new_ready = False
        for task in sorted_tasks:
            if all(dep not in active_tasks and dep != task for dep in tasks[task][1]):
                ready_queue.append(task)
                new_ready = True

        # Если ни одна задача не готова к выполнению, ждем следующего цикла
        if not new_ready and not ready_queue:
            continue

        # Выполняем задачи по правилам
        while available_workers > 0 and ready_queue:
            current_task = ready_queue.popleft()
            active_tasks.add(current_task)
            result.append((current_time, current_task))
            current_time += task_duration[current_task]
            available_workers -= 1

    # Проверка на завершение всех задач
    if len(result) != sum(1 for _ in tasks.values()):
        return None

    # Сортируем результаты по времени старта и возвращаем задачи в порядке выполнения
    result.sort()
    return [task for time, task in result]
