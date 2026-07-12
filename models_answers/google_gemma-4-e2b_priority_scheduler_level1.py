import heapq
from collections import deque

def plan_order(tasks: dict[str, tuple[int, list[str], int]], workers: int) -> list[str] | None:
    """
    Планировщик задач с зависимостями, приоритетами и ограниченным числом исполнителей.

    tasks: {task_name: (duration, deps, priority)}
    workers: Максимальное число одновременно выполняющихся задач.
    Возвращает: Список задач в порядке их завершения. Возвращает None при наличии цикла.
    """
    if not tasks:
        return []

    # --- 1. Инициализация и построение графа ---
    task_data = {}
    adj = {}  # Граф зависимостей (кто зависит от меня)
    in_degree = {} # Количество незавершенных зависимостей
    all_task_names = set(tasks.keys())

    for name, (duration, deps, priority) in tasks.items():
        task_data[name] = {
            'duration': duration,
            'deps': set(deps),
            'priority': priority,
            'status': 'pending',  # pending, ready, running, completed
            'start_time': -1,
            'finish_time': -1
        }
        adj[name] = []
        in_degree[name] = len(deps)

    # Построение списка смежности и начальных в-градов
    for name, data in task_data.items():
        for dep in data['deps']:
            if dep not in all_task_names:
                # Ошибка: зависимость от несуществующей задачи
                return None
            adj[dep].append(name)

    # --- 2. Инициализация очередей и структур данных для симуляции ---
    
    # Очередь задач, готовых к запуску (используем min-heap для приоритетной сортировки)
    # Элемент: (-priority, duration, name) -> Максимум priority, минимум duration, минимум имя.
    ready_queue = [] 

    # Задачи, которые должны быть выполнены (для отслеживания завершения)
    running_tasks = {}  # {task_name: finish_time}
    completed_tasks = []
    current_time = 0
    
    # Инициализация ready_queue с задач, у которых нет зависимостей
    for name in all_task_names:
        if in_degree[name] == 0:
            duration = task_data[name]['duration']
            priority = task_data[name]['priority']
            
            # heapq использует минимальный порядок. Для приоритета (максимум) используем отрицание.
            # Затем duration (минимум), затем имя (минимум).
            heapq.heappush(ready_queue, (-priority, duration, name))

    # --- 3. Основной цикл симуляции ---
    
    while len(completed_tasks) < len(all_task_names):
        
        # A. Запуск новых задач (если есть свободные исполнители и готовые задачи)
        while workers > 0 and ready_queue:
            # Извлекаем лучшую задачу согласно правилам: (-priority, duration, name)
            neg_p, dur, name = heapq.heappop(ready_queue)
            workers -= 1

            task = task_data[name]
            start_time = current_time
            finish_time = start_time + task['duration']
            
            task['status'] = 'running'
            task['start_time'] = start_time
            task['finish_time'] = finish_time
            
            running_tasks[name] = finish_time

            # Добавляем в очередь завершения (для сортировки по времени)
            heapq.heappush(ready_queue, (finish_time, name)) # Используем отдельный heap для событий

        # B. Переход во время следующего события (завершение задачи)
        if not running_tasks:
            # Если нет запущенных задач и очередь пуста, но задачи еще не завершены, 
            # это означает либо цикл, либо ошибка в логике (но мы проверим цикл ниже).
            if len(completed_tasks) < len(all_task_names):
                # Если есть незавершенные задачи, но ничего не запущено и ничего не готово - цикл.
                return None 
            break

        # Находим следующее событие (минимальное время завершения среди запущенных задач)
        next_event_time = float('inf')
        for finish_time in running_tasks.values():
            if finish_time < next_event_time:
                next_event_time = finish_time

        current_time = next_event_time

        # C. Обработка завершенных задач и обновление зависимостей
        newly_completed = []
        for name, finish_time in list(running_tasks.items()):
            if finish_time <= current_time:
                task = task_data[name]
                task['status'] = 'completed'
                completed_tasks.append(name)
                del running_tasks[name]
                newly_completed.append(name)

        # Обновление в-градов для зависимых задач
        for completed_name in newly_completed:
            for dependent_name in adj[completed_name]:
                in_degree[dependent_name] -= 1
                if in_degree[dependent_name] == 0:
                    # Задача готова к запуску
                    dep_task = task_data[dependent_name]
                    heapq.heappush(ready_queue, (-dep_task['priority'], dep_task['duration'], dependent_name))

    if len(completed_tasks) == len(all_task_names):
        # Возвращаем порядок завершения
        return completed_tasks
    else:
        # Если цикл был обнаружен (хотя в данной реализации это должно быть поймано через in_degree), 
        # возвращаем None.
        return None
