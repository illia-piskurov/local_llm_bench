def critical_path(tasks: dict[str, tuple[int, list[str]]]) -> int | None:
    # Используем функцию topo_sort для получения топологической сортировки задач
    topological_order = topo_sort(tasks)
    
    if topological_order is None:
        return None

    # Создаем граф зависимостей
    graph = defaultdict(list)
    for task, (duration, dependencies) in tasks.items():
        for dependency in dependencies:
            graph[dependency].append(task)

    # Функция для расчёта максимальной длины пути от заданной задачи
    def longest_path(node):
        if node not in tasks:
            return 0
        duration, _ = tasks[node]
        max_duration = duration
        for neighbor in graph[node]:
            max_duration = max(max_duration, longest_path(neighbor) + duration)
        return max_duration

    # Вычисляем длину критического пути
    critical_path_length = 0
    for task in topological_order:
        critical_path_length = max(critical_path_length, longest_path(task))

    return critical_path_length
