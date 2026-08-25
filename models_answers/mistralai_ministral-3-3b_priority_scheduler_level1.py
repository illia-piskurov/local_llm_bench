from collections import deque

def plan_order(tasks: dict[str, tuple[int, list[str], int]], workers: int) -> list[str] | None:
    # Проверка на циклы зависимостей
    visited = set()
    recursion_stack = set()

    def has_cycle(task):
        if task in recursion_stack:
            return True
        if task in visited:
            return False
        visited.add(task)
        recursion_stack.add(task)
        for dep in tasks.get(task, (0, [], 0))[1]:
            if has_cycle(dep):
                return True
        recursion_stack.remove(task)
        return False

    for task in tasks:
        if has_cycle(task):
            return None

    # Сортировка задач по приоритету и длительности
    sorted_tasks = sorted(tasks.keys(), key=lambda x: (-tasks[x][2], tasks[x][0], x))

    ready_queue = deque()
    task_duration = {task: duration for task, (duration, _, _) in tasks.items()}
    available_workers = workers

    result = []
    current_time = 0
    active_tasks = set()

    while ready_queue or active_tasks:
        # Определяем задачи, готовые к выполнению в текущий момент времени
        for task in sorted_tasks:
            if all(dep not in active_tasks and dep != task for dep in tasks[task][1]):
                ready_queue.append(task)

        # Выполняем задачи по правилам
        while available_workers > 0 and ready_queue:
            current_task = ready_queue.popleft()
            if current_task in active_tasks:
                continue

            active_tasks.add(current_task)
            result.append((current_time, current_task))
            current_time += task_duration[current_task]
            available_workers -= 1

        # Если нет свободных рабочих мест и все задачи выполнены
        if not ready_queue and not active_tasks:
            break

    # Проверка на завершение всех задач
    if len(result) != sum(1 for _ in tasks.values()):
        return None

    # Сортируем результаты по времени старта и возвращаем задачи в порядке выполнения
    result.sort()
    return [task for time, task in result]
