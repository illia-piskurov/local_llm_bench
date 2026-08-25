def critical_path(tasks: dict[str, tuple[int, list[str], int]]) -> int | None:
    from collections import defaultdict, deque

    indegree = defaultdict(int)
    graph = defaultdict(list)
    durations = {}
    all_tasks = set(tasks.keys())

    for task, (dur, deps, _) in tasks.items():
        durations[task] = dur
        indegree[task] = len(deps)
        for dep in deps:
            if dep not in all_tasks:
                return None
            graph[dep].append(task)

    # Копия индексов для проверки циклов
    indeg = indegree.copy()
    q = deque([t for t in all_tasks if indeg[t] == 0])
    processed = 0
    while q:
        node = q.popleft()
        processed += 1
        for nxt in graph[node]:
            indeg[nxt] -= 1
            if indeg[nxt] == 0:
                q.append(nxt)

    if processed != len(tasks):
        return None

    # Длинна самого длинного пути (без учета приоритета)
    dist = {t: 0 for t in tasks}
    q = deque([t for t in all_tasks if indegree[t] == 0])
    while q:
        node = q.popleft()
        for nxt in graph[node]:
            if dist[nxt] < dist[node] + durations[node]:
                dist[nxt] = dist[node] + durations[node]
            indegree[nxt] -= 1
            if indegree[nxt] == 0:
                q.append(nxt)

    return max(dist.values()) if dist else 0


def makespan(tasks: dict[str, tuple[int, list[str], int]], workers: int) -> int | None:
    from collections import defaultdict, deque
    import heapq

    indegree = defaultdict(int)
    graph = defaultdict(list)
    durations = {}
    priorities = {}
    all_tasks = set(tasks.keys())

    for task, (dur, deps, prio) in tasks.items():
        durations[task] = dur
        priorities[task] = prio
        indegree[task] = len(deps)
        for d in deps:
            if d not in all_tasks:
                return None
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
        current = []
        while ready and len(current) < available_workers:
            _, _, task = heapq.heappop(ready)
            if indegree[task] == 0 and task not in completed:
                current.append(task)
                for nxt in graph[task]:
                    indegree[nxt] -= 1
                    if indegree[nxt] == 0:
                        heapq.heappush(ready, (-priorities[nxt], durations[nxt], nxt))

        # Сортируем текущие задачи по правилу: priority↑, duration↓, name↑
        current.sort(key=lambda x: (-priorities[x], durations[x], x))
        for task in current:
            result.append(task)
            completed.add(task)
            available_workers -= 1

        if not current:
            # Переходим к следующему времени (по минимальному временному метку)
            next_time = None
            for t in all_tasks:
                if t not in completed and indegree[t] == 0:
                    # Время запуска — текущее время + 1 (задача выполняется за 1 единицу)
                    next_time = time + 1
                    break
            if next_time is None:
                break
            time = next_time
            available_workers = sum(1 for t in ready if t[2] not in completed)
            continue

        # Проверяем циклы: если остались задачи с индексом > 0, но нет готовых
        if any(indegree[t] > 0 for t in all_tasks):
            return None

        time += 1  # Время проходит

    if len(completed) != len(tasks):
        return None

    return time
