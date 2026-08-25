def plan_order(tasks: dict[str, tuple[int, list[str], int]], workers: int) -> list[str] | None:
    from collections import defaultdict, deque
    import heapq

    # Построение графа зависимостей и индексации задач
    indegree = defaultdict(int)
    graph = defaultdict(list)
    durations = {}
    priorities = {}
    all_tasks = set(tasks.keys())

    for task, (_, deps, prio) in tasks.items():
        durations[task] = task
        priorities[task] = prio
        indegree[task] = len(deps)
        for d in deps:
            if d not in all_tasks:
                return None  # Непонятная задача в зависимостях
            graph[d].append(task)

    # Начальные задачи (без зависимостей)
    ready = []
    for task, deg in indegree.items():
        if deg == 0:
            heapq.heappush(ready, (-priorities[task], durations[task], task))

    time = 0
    result = []
    available_workers = workers
    completed = set()

    while ready or any(indegree[t] > 0 for t in all_tasks):
        # Собираем задачи, которые могут начаться сейчас
        current = []
        while ready and len(current) < available_workers:
            _, _, task = heapq.heappop(ready)
            if indegree[task] == 0 and task not in completed:
                current.append(task)
                # Уменьшаем индексы зависимостей для всех соседей
                for nxt in graph[task]:
                    indegree[nxt] -= 1
                    if indegree[nxt] == 0:
                        heapq.heappush(ready, (-priorities[nxt], durations[nxt], nxt))
        # Добавляем готовые задачи к результату (по правилу сортировки)
        current.sort(key=lambda x: (-priorities[x], durations[x], x))
        for task in current:
            result.append(task)
            completed.add(task)
            available_workers -= 1
            # Удаляем задачу из доступных
            ready = [t for t in ready if t[2] != task]
            heapq.heapify(ready)
        # Переходим к следующему времени (все готовые заработают сразу)
        if current:
            time += 1
            available_workers = workers - sum(1 for t in ready if t[2] not in completed)
        else:
            # Если ничего не готово, прыгаем по времени к следующей задаче
            next_time = min((t for _, _, t in ready if t not in completed), default=None, key=lambda x: (x not in completed, x))
            if next_time is None:
                break
            time = next_time
            # Перезапускаем цикл с новым временем
            continue

        # Проверяем циклы: если остались задачи с индексом > 0, но нет готовых
        if any(indegree[t] > 0 for t in all_tasks):
            return None

    # Проверяем, выполнены ли все задачи
    if len(completed) != len(tasks):
        return None

    return result
