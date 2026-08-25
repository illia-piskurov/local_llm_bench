import heapq
from collections import defaultdict

def plan_order(tasks: dict[str, tuple[int, list[str], int]], workers: int) -> list[str] | None:
    """
    Планировщик задач с зависимостями, приоритетами и ограниченным числом исполнителей.

    Args:
        tasks: Словарь, где ключ - имя задачи, а значение - кортеж (duration, deps, priority).
        workers: Максимальное число одновременно выполняющихся задач.

    Returns:
        Список имен задач в порядке их выполнения, или None, если цикл зависимостей обнаружен.
    """
    if not tasks:
        return []

    # 1. Инициализация данных и графа
    task_data = {}
    dependencies = defaultdict(set)
    in_degree = defaultdict(int)
    all_task_names = set()

    for name, (duration, deps, priority) in tasks.items():
        task_data[name] = {
            'duration': duration,
            'deps': set(deps),
            'priority': priority,
            'status': 'pending',  # pending, ready, running, finished
            'start_time': -1,
            'finish_time': -1
        }
        all_task_names.add(name)

    # Построение графа и расчет вхождений (in-degrees)
    for name, data in task_data.items():
        in_degree[name] = len(data['deps'])

    # 2. Инициализация очередей
    # Ready Queue: Используем min-heap для приоритетов.
    # Приоритет сортировки: (-priority, duration, name)
    ready_queue = []  # ( -priority, duration, name )
    
    # Задачи, готовые к запуску (в порядке приоритета)
    for name in all_task_names:
        if in_degree[name] == 0:
            duration = task_data[name]['duration']
            priority = task_data[name]['priority']
            
            # Вставляем в кучу для сортировки по правилам:
            # 1. Максимальный priority (т.е. минимальное -priority)
            # 2. Минимальная duration
            # 3. Минимальное имя (лексикографический порядок)
            heapq.heappush(ready_queue, (-priority, duration, name))

    running_tasks = []  # Список задач, которые сейчас выполняются: (finish_time, task_name)
    scheduled_order = []
    current_time = 0
    
    # 3. Основной цикл планирования
    while ready_queue or running_tasks:
        
        # A. Обработка завершенных задач и обновление времени
        if running_tasks:
            # Находим следующее событие (самое раннее завершение)
            next_finish_time = min(ft for ft, _ in running_tasks)
            current_time = max(current_time, next_finish_time)

            newly_finished = []
            
            # Определяем задачи, которые завершились на current_time
            running_tasks_to_keep = []
            for finish_time, task_name in running_tasks:
                if finish_time <= current_time:
                    newly_finished.append(task_name)
                else:
                    running_tasks_to_keep.append((finish_time, task_name))
            
            running_tasks = running_tasks_to_keep

            # Обработка завершенных задач
            for task_name in newly_finished:
                task_data[task_name]['status'] = 'finished'
                scheduled_order.append(task_name)
                
                # Обновляем зависимости для зависимых задач
                for dependent_name in all_task_names:
                    if task_name in task_data[dependent_name]['deps']:
                        task_data[dependent_name]['deps'].remove(task_name)
                        if not task_data[dependent_name]['deps']:
                            # Задача стала готова
                            duration = task_data[dependent_name]['duration']
                            priority = task_data[dependent_name]['priority']
                            heapq.heappush(ready_queue, (-priority, duration, dependent_name))

        # B. Запуск новых задач (если есть свободные исполнители и задачи в очереди)
        while ready_queue and len(running_tasks) < workers:
            # Извлекаем задачу с наивысшим приоритетом
            neg_p, dur, name = heapq.heappop(ready_queue)
            
            if task_data[name]['status'] != 'pending':
                continue # Уже запущена или завершена ранее (хотя это маловероятно в этой структуре)

            # Запуск задачи
            task_data[name]['status'] = 'running'
            task_data[name]['start_time'] = current_time
            finish_time = current_time + dur
            task_data[name]['finish_time'] = finish_time
            
            # Добавляем в список текущих исполнителей
            heapq.heappush(running_tasks, (finish_time, name))

        # Если нет задач, которые могут быть запущены и нет выполняющихся, но есть задачи в очереди, 
        # это означает, что мы ждем завершения. В этом случае цикл будет продолжаться на следующем шаге.
        if not running_tasks and ready_queue:
            # Этого не должно произойти, если current_time был обновлен корректно, но для безопасности
            current_time += 1


    # 4. Проверка на циклы и возврат результата
    if len(scheduled_order) != len(all_task_names):
        # Если не все задачи были запланированы, значит, есть цикл (или недостижимые зависимости)
        return None

    return scheduled_order

if __name__ == '__main__':
    # Пример 1: Простая цепочка с приоритетами
    tasks1 = {
        "A": (5, [], 10),  # Duration=5, Deps=[], Priority=10
        "B": (3, ["A"], 5), # Duration=3, Deps=["A"], Priority=5
        "C": (2, ["A"], 8)  # Duration=2, Deps=["A"], Priority=8
    }
    workers1 = 2
    # Ожидаемый порядок: A -> C (P=8, D=2) -> B (P=5, D=3)
    result1 = plan_order(tasks1, workers1)
    print("--- Пример 1 ---")
    print(f"Результат: {result1}") # Ожидаем ['A', 'C', 'B'] или ['A', 'B', 'C'] в зависимости от правил.

    # Пример 2: Конфликт приоритетов и ограничение исполнителей
    tasks2 = {
        "T1": (10, [], 5),  # P=5
        "T2": (2, [], 10),   # P=10 (должна идти первой)
        "T3": (4, ["T1"], 8), # Зависит от T1
        "T4": (3, ["T1"], 9)  # Зависит от T1
    }
    workers2 = 1
    # Ожидаемый порядок: T2 (P=10) -> T1 (P=5). Затем T3 или T4.
    result2 = plan_order(tasks2, workers2)
    print("\n--- Пример 2 ---")
    print(f"Результат: {result2}") # Ожидаем [T2, T1, T3/T4]

    # Пример 3: Цикл зависимостей
    tasks3 = {
        "X": (5, ["Y"], 1),
        "Y": (5, ["X"], 1)
    }
    workers3 = 1
    result3 = plan_order(tasks3, workers3)
    print("\n--- Пример 3 (Цикл) ---")
    print(f"Результат: {result3}") # Ожидаем None
