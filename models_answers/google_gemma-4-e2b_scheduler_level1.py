def topo_sort(tasks: dict[str, list[str]]) -> list[str] | None:
    """
    Выполняет топологическую сортировку графа зависимостей с использованием алгоритма Кана.

    Args:
        tasks: Словарь, где ключ — имя задачи, а значение — список имён задач, 
               от которых она зависит (предшественники).

    Returns:
        Список имён задач в порядке выполнения, или None, если в графе есть цикл зависимостей.
    """
    
    # 1. Инициализация структуры данных и сбор всех узлов
    adj = {}       # Граф смежности (предшественник -> зависимая задача)
    in_degree = {} # Входящая степень (количество зависимостей для каждой задачи)
    all_tasks = set()

    # Добавляем все задачи в структуру, чтобы учесть и те, что не имеют явных зависимостей
    for task in tasks:
        all_tasks.add(task)
        if task not in adj:
            adj[task] = []
            in_degree[task] = 0

    # 2. Построение графа и расчет входящих степеней
    for dependent_task, prerequisites in tasks.items():
        for prereq in prerequisites:
            # Создаем ребро: prereq -> dependent_task
            if prereq not in adj:
                adj[prereq] = []
                in_degree[prereq] = 0
            
            # Добавляем ребро в граф (предшественник -> зависимая задача)
            adj[prereq].append(dependent_task)
            
            # Увеличиваем входящую степень зависимой задачи
            in_degree[dependent_task] += 1

    # Если есть задачи, которые не фигурируют ни в качестве ключей, ни в значениях (т.е., они существуют только как зависимости),
    # мы должны убедиться, что они включены в in_degree и adj.
    for task in all_tasks:
        if task not in in_degree:
            in_degree[task] = 0
        if task not in adj:
            adj[task] = []


    # 3. Алгоритм Кана (Kahn's Algorithm)
    queue = []
    
    # Инициализация очереди задачами с нулевой входящей степенью
    for task, degree in in_degree.items():
        if degree == 0:
            queue.append(task)

    sorted_order = []
    
    while queue:
        u = queue.pop(0)  # Извлекаем задачу
        sorted_order.append(u)

        # Обрабатываем всех соседей (зависимых задач)
        for v in adj[u]:
            in_degree[v] -= 1
            if in_degree[v] == 0:
                queue.append(v)

    # 4. Проверка на наличие цикла
    # Если количество отсортированных задач меньше общего количества уникальных задач, то цикл существует.
    if len(sorted_order) != len(all_tasks):
        return None  # Цикл обнаружен
    else:
        return sorted_order

if __name__ == '__main__':
    # Пример 1: Правильная зависимость (A зависит от B, B зависит от C)
    tasks1 = {
        'A': ['B'],
        'B': ['C'],
        'C': []
    }
    print(f"Пример 1: {topo_sort(tasks1)}")  # Ожидаемый результат: ['C', 'B', 'A']

    # Пример 2: Параллельные задачи (A и B не зависят друг от друга)
    tasks2 = {
        'A': ['C'],
        'B': ['C'],
        'C': []
    }
    print(f"Пример 2: {topo_sort(tasks2)}")  # Ожидаемый результат: ['C', 'A', 'B'] или ['C', 'B', 'A']

    # Пример 3: Цикл зависимостей (A зависит от B, B зависит от A)
    tasks3 = {
        'A': ['B'],
        'B': ['A']
    }
    print(f"Пример 3 (Цикл): {topo_sort(tasks3)}")  # Ожидаемый результат: None

    # Пример 4: Пустой граф
    tasks4 = {}
    print(f"Пример 4 (Пустой): {topo_sort(tasks4)}") # Ожидаемый результат: []
