from collections import defaultdict, deque
from typing import Dict, List, Optional

def topo_sort(tasks: Dict[str, List[str]]) -> Optional[List[str]]:
    """
    Выполняет топологическую сортировку задач с учетом их зависимостей.

    Args:
        tasks: Словарь, где ключ — имя задачи (строка), а значение — список 
               имён задач, от которых она зависит (предшественники).

    Returns:
        Список имён всех задач в порядке выполнения, или None, если обнаружен цикл.
    """
    
    # 1. Инициализация графа и подсчет in-degrees
    
    # adj[P] = [T1, T2, ...] означает, что задачи T1, T2... зависят от P (P -> Ti)
    adj: Dict[str, List[str]] = defaultdict(list)
    in_degree: Dict[str, int] = {}
    all_tasks: set[str] = set()

    # Сбор всех уникальных задач и инициализация in_degree для каждой задачи
    for task, prerequisites in tasks.items():
        all_tasks.add(task)
        for prereq in prerequisites:
            all_tasks.add(prereq)
            
    # Инициализируем in_degree для всех задач нулем
    for task in all_tasks:
        in_degree[task] = 0

    # Построение графа и подсчет входов (in-degrees)
    for task, prerequisites in tasks.items():
        for prereq in prerequisites:
            # Ребро идет от prereq к task (prereq -> task)
            adj[prereq].append(task)
            # Увеличиваем степень входа для 'task'
            in_degree[task] += 1

    # 2. Инициализация очереди с задачами, у которых нет зависимостей (in_degree == 0)
    queue = deque()
    for task in all_tasks:
        if in_degree[task] == 0:
            queue.append(task)

    # 3. Выполнение топологической сортировки (Kahn's Algorithm)
    sorted_order: List[str] = []
    
    while queue:
        u = queue.popleft()
        sorted_order.append(u)
        
        # Обрабатываем всех соседей (задач, которые зависят от u)
        for v in adj[u]:
            # Уменьшаем степень входа для задачи v
            in_degree[v] -= 1
            
            # Если у v больше нет незавершенных зависимостей, добавляем ее в очередь
            if in_degree[v] == 0:
                queue.append(v)

    # 4. Проверка на циклы
    if len(sorted_order) != len(all_tasks):
        # Если количество задач в порядке меньше общего числа, значит, есть цикл
        return None
    else:
        return sorted_order

if __name__ == '__main__':
    # Пример 1: Корректный порядок
    print("--- Тест 1: Успешная сортировка ---")
    tasks1 = {
        "C": ["A", "B"],
        "D": ["A"],
        "E": [] # Задача без зависимостей
    }
    result1 = topo_sort(tasks1)
    print(f"Задачи: {tasks1}")
    print(f"Результат (ожидается порядок, где A и B идут до C): {result1}")

    # Пример 2: Цикл зависимостей (A -> B -> C -> A)
    print("\n--- Тест 2: Обнаружение цикла ---")
    tasks2 = {
        "A": ["C"],
        "B": ["A"],
        "C": ["B"]
    }
    result2 = topo_sort(tasks2)
    print(f"Задачи: {tasks2}")
    print(f"Результат (ожидается None): {result2}")

    # Пример 3: Сложный граф с несколькими независимыми ветвями
    print("\n--- Тест 3: Сложный граф ---")
    tasks3 = {
        "Task_Z": ["A", "B"],
        "Task_Y": ["C"],
        "Task_X": []
    }
    # Граф: A->Z, B->Z, C->Y. X - независима.
    result3 = topo_sort(tasks3)
    print(f"Задачи: {tasks3}")
    print(f"Результат (должен быть корректным): {result3}")

    # Пример 4: Задача без зависимостей, но упоминается как зависимость для другой задачи
    print("\n--- Тест 4: Независимая задача ---")
    tasks4 = {
        "Task_Final": ["Start"],
        "Task_Mid": []
    }
    # Граф: Start -> Task_Final. Task_Mid - независима.
    result4 = topo_sort(tasks4)
    print(f"Задачи: {tasks4}")
    print(f"Результат (должен включать Start и Task_Mid): {result4}")
