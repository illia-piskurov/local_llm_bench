def topo_sort(tasks: dict[str, list[str]]) -> list[str] | None:
    if not tasks:
        return []
    
    # Собираем все задачи
    all_tasks = set(tasks.keys())
    for deps in tasks.values():
        all_tasks.update(deps)
    
    # Если задач нет, возвращаем пустой список
    if not all_tasks:
        return []
    
    # Словарь для хранения входящих степеней (количество зависимостей)
    in_degree = {}
    for task in all_tasks:
        in_degree[task] = 0
    
    # Устанавливаем входящие степени
    for task, deps in tasks.items():
        for dep in deps:
            in_degree[dep] += 1
    
    # Начинаем с задач, у которых входящий степень 0
    queue = []
    for task in all_tasks:
        if in_degree[task] == 0:
            queue.append(task)
    
    result = []
    
    # Проводим топологическую сортировку
    while queue:
        # Берём задачу с нулевым входящим степенем
        current = queue.pop(0)
        result.append(current)
        
        # Обновляем входящие степени для всех задач, которые зависят от текущей
        for next_task in tasks.get(current, []):
            in_degree[next_task] -= 1
            # Если входящий степень стала 0, добавляем в очередь
            if in_degree[next_task] == 0:
                queue.append(next_task)
    
    # Если результат не содержит все задачи — есть цикл
    if len(result) != len(all_tasks):
        return None
    
    return result
