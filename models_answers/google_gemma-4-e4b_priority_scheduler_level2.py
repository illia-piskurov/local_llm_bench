import collections
from typing import List, Dict, Tuple, Optional

def plan_order(tasks: dict[str, tuple[int, list[str], int]], workers: int) -> Optional[List[str]]:
    """
    Планирует выполнение задач с учетом зависимостей, приоритетов и ограниченного числа исполнителей.

    Args:
        tasks: Словарь {task_name: (duration, dependencies, priority)}.
        workers: Максимальное количество одновременно работающих задач.

    Returns:
        Список имен задач в порядке их старта, или None если обнаружен цикл зависимостей.
    """

    # --- 1. Cycle Detection and Graph Setup ---
    adj = collections.defaultdict(list)
    in_degree = {task: 0 for task in tasks}
    
    for task_name, (_, deps, _) in tasks.items():
        for dep in deps:
            if dep not in tasks:
                # Dependency listed but not defined
                return None 
            adj[dep].append(task_name)
            in_degree[task_name] += 1

    # Kahn's algorithm for cycle detection (Topological Sort check)
    temp_in_degree = dict(in_degree)
    q_check = collections.deque([task for task in tasks if temp_in_degree[task] == 0])
    processed_count = 0

    while q_check:
        u = q_check.popleft()
        processed_count += 1
        
        for v in adj[u]:
            temp_in_degree[v] -= 1
            if temp_in_degree[v] == 0:
                q_check.append(v)

    if processed_count != len(tasks):
        return None # Cycle detected

    # --- 2. Simulation Setup ---
    
    completed_tasks = set()
    running_tasks: Dict[str, int] = {}  # {task_name: finish_time}
    scheduled_order: List[str] = []
    current_time = 0

    eligible_tasks = set(task for task in tasks if not tasks[task][1])
    remaining_tasks = set(tasks.keys())

    while remaining_tasks:
        
        # --- A. Process Completions and Update Dependencies ---
        if running_tasks:
            min_finish_time = min(running_tasks.values())
            
            # Advance time to the next completion event
            current_time = max(current_time, min_finish_time)

            finished_this_step = []
            for task_name, finish_time in list(running_tasks.items()):
                if finish_time <= current_time:
                    finished_this_step.append(task_name)
                    del running_tasks[task_name]
                    completed_tasks.add(task_name)

            # Update eligibility based on completions
            for finished_task in finished_this_step:
                for successor in adj[finished_task]:
                    if successor not in completed_tasks and successor not in running_tasks:
                        _, deps, _ = tasks[successor]
                        if all(dep in completed_tasks for dep in deps):
                            eligible_tasks.add(successor)

        # --- B. Scheduling Phase ---
        available_workers = workers - len(running_tasks)
        
        candidates = list(eligible_tasks)
        
        if candidates:
            # Apply selection rules:
            # 1. Highest Priority (descending) -> -priority
            # 2. Shortest Duration (ascending) -> duration
            # 3. Alphabetical Name (ascending) -> name
            def sort_key(task_name):
                duration, _, priority = tasks[task_name]
                return (-priority, duration, task_name)

            candidates.sort(key=sort_key)
            
            tasks_to_start = candidates[:available_workers]

            # Record the start event and update state
            if tasks_to_start:
                scheduled_order.extend(tasks_to_start) 
                
                for task_name in tasks_to_start:
                    duration, _, _ = tasks[task_name]
                    finish_time = current_time + duration
                    running_tasks[task_name] = finish_time
                    eligible_tasks.remove(task_name)

        # --- C. Termination Check ---
        if not running_tasks and not eligible_tasks and remaining_tasks:
            break 

    return scheduled_order if len(completed_tasks) == len(tasks) else None


def critical_path(tasks: dict[str, tuple[int, list[str], int]]) -> Optional[int]:
    """
    Вычисляет длину самого длинного зависимого пути (критический путь) 
    по сумме длительностей задач.

    Args:
        tasks: Словарь {task_name: (duration, dependencies, priority)}.

    Returns:
        Длина критического пути или None, если обнаружен цикл.
    """
    memo = {}  # Memoization for longest path ending at task T
    recursion_stack = set() # For cycle detection

    def dfs(task_name):
        if task_name in memo:
            return memo[task_name]
        
        if task_name in recursion_stack:
            raise ValueError("Cycle detected")
        
        duration, deps, _ = tasks[task_name]
        
        recursion_stack.add(task_name)
        max_predecessor_path = 0
        
        for dep in deps:
            # Recursively find the longest path ending at the dependency
            try:
                path_len = dfs(dep)
                max_predecessor_path = max(max_predecessor_path, path_len)
            except ValueError:
                raise # Propagate cycle detection error

        recursion_stack.remove(task_name)
        
        # Longest path ending at task T = Duration(T) + Max(Longest paths of dependencies)
        result = duration + max_predecessor_path
        memo[task_name] = result
        return result

    try:
        max_critical_path = 0
        for task_name in tasks:
            # Calculate the longest path ending at this task
            length = dfs(task_name)
            max_critical_path = max(max_critical_path, length)
        return max_critical_path
    except ValueError:
        return None # Cycle detected


def makespan(tasks: dict[str, tuple[int, list[str], int]], workers: int) -> Optional[int]:
    """
    Вычисляет общее время завершения всех задач (makespan), 
    используя логику планирования из plan_order.

    Args:
        tasks: Словарь {task_name: (duration, dependencies, priority)}.
        workers: Максимальное количество одновременно работающих задач.

    Returns:
        Общее время завершения всех задач или None, если обнаружен цикл.
    """
    # --- 1. Cycle Detection and Graph Setup (Reused from plan_order) ---
    adj = collections.defaultdict(list)
    in_degree = {task: 0 for task in tasks}
    
    for task_name, (_, deps, _) in tasks.items():
        for dep in deps:
            if dep not in tasks: return None
            adj[dep].append(task_name)
            in_degree[task_name] += 1

    temp_in_degree = dict(in_degree)
    q_check = collections.deque([task for task in tasks if temp_in_degree[task] == 0])
    processed_count = 0

    while q_check:
        u = q_check.popleft()
        processed_count += 1
        for v in adj[u]:
            temp_in_degree[v] -= 1
            if temp_in_degree[v] == 0:
                q_check.append(v)

    if processed_count != len(tasks):
        return None # Cycle detected

    # --- 2. Simulation Setup (Modified from plan_order) ---
    
    completed_tasks = set()
    running_tasks: Dict[str, int] = {}  # {task_name: finish_time}
    current_time = 0
    eligible_tasks = set(task for task in tasks if not tasks[task][1])
    remaining_tasks = set(tasks.keys())

    while remaining_tasks:
        
        # A. Process Completions and Update Dependencies
        if running_tasks:
            min_finish_time = min(running_tasks.values())
            current_time = max(current_time, min_finish_time)

            finished_this_step = []
            for task_name, finish_time in list(running_tasks.items()):
                if finish_time <= current_time:
                    finished_this_step.append(task_name)
                    del running_tasks[task_name]
                    completed_tasks.add(task_name)

            for finished_task in finished_this_step:
                for successor in adj[finished_task]:
                    if successor not in completed_tasks and successor not in running_tasks:
                        _, deps, _ = tasks[successor]
                        if all(dep in completed_tasks for dep in deps):
                            eligible_tasks.add(successor)

        # B. Scheduling Phase
        available_workers = workers - len(running_tasks)
        candidates = list(eligible_tasks)
        
        if candidates:
            def sort_key(task_name):
                duration, _, priority = tasks[task_name]
                return (-priority, duration, task_name)

            candidates.sort(key=sort_key)
            
            tasks_to_start = candidates[:available_workers]

            if tasks_to_start:
                for task_name in tasks_to_start:
                    duration, _, _ = tasks[task_name]
                    finish_time = current_time + duration
                    running_tasks[task_name] = finish_time
                    eligible_tasks.remove(task_name)

        # C. Termination Check
        if not running_tasks and not eligible_tasks and remaining_tasks:
            break 

    if len(completed_tasks) != len(tasks):
        return None # Cycle or unfinishable state

    # Makespan is the time when the last task finishes
    return max(running_tasks.values()) if running_tasks else current_time


if __name__ == '__main__':
    # Example 1: Basic sequential execution (Duration=5+3+2 = 10)
    tasks1 = {
        "A": (5, [], 1),
        "B": (3, ["A"], 2),
        "C": (2, ["B"], 3)
    }
    workers1 = 1
    print("--- Example 1: Plan Order ---")
    result_plan1 = plan_order(tasks1, workers1)
    print(f"Plan Order Result: {result_plan1}")
    print(f"Critical Path: {critical_path(tasks1)}") # Expected: 10
    print(f"Makespan (W=1): {makespan(tasks1, workers1)}") # Expected: 10

    # Example 2: Parallel execution (T1 and T2 run in parallel)
    tasks2 = {
        "T1": (5, [], 1),
        "T2": (3, [], 2),
        "T3": (7, ["T1"], 3)
    }
    workers2 = 2
    print("\n--- Example 2: Plan Order ---")
    result_plan2 = plan_order(tasks2, workers2)
    # T=0: Start T2 (P=2), T1 (P=1). Order: ['T2', 'T1']
    print(f"Plan Order Result: {result_plan2}") 
    print(f"Critical Path: {critical_path(tasks2)}") # Expected: T1 -> T3 = 5 + 7 = 12
    print(f"Makespan (W=2): {makespan(tasks2, workers2)}") # Expected: 12

    # Example 3: Complex scheduling and tie-breaking
    tasks3 = {
        "A": (5, [], 1),  # P=1, D=5
        "B": (2, [], 2),  # P=2, D=2 -> Should start first
        "C": (4, ["B"], 3) # Must wait for B
    }
    workers3 = 2
    print("\n--- Example 3: Plan Order ---")
    result_plan3 = plan_order(tasks3, workers3)
    # T=0: Candidates A, B. Select B (P=2), then A (P=1). Start order: ['B', 'A']
    print(f"Plan Order Result: {result_plan3}") 
    print(f"Critical Path: {critical_path(tasks3)}") # Expected: B -> C = 2 + 4 = 6
    print(f"Makespan (W=2): {makespan(tasks3, workers3)}") # Expected: A finishes at 5. C starts at 2 and finishes at 6. Max finish time is 6.

    # Example 4: Cycle detection
    tasks4 = {
        "X": (1, ["Y"], 1),
        "Y": (1, ["Z"], 1),
        "Z": (1, ["X"], 1)
    }
    workers4 = 3
    print("\n--- Example 4: Cycle Detection ---")
    result_plan4 = plan_order(tasks4, workers4)
    print(f"Plan Order Result: {result_plan4}")
    print(f"Critical Path: {critical_path(tasks4)}") # Expected: None
    print(f"Makespan (W=3): {makespan(tasks4, workers4)}") # Expected: None

    # Example 5: Workers limit forcing sequential start
    tasks5 = {
        "A": (10, [], 3),
        "B": (10, [], 2),
        "C": (10, [], 1)
    }
    workers5 = 1
    print("\n--- Example 5: Workers Limit=1 ---")
    result_plan5 = plan_order(tasks5, workers5)
    # Order: A (P=3), B (P=2), C (P=1). All start sequentially.
    print(f"Plan Order Result: {result_plan5}") 
    print(f"Critical Path: {critical_path(tasks5)}") # Expected: 10
    print(f"Makespan (W=1): {makespan(tasks5, workers5)}") # Expected: 30

    # Example 6: Multiple tasks ready at T=0 with same priority/duration
    tasks6 = {
        "Z": (5, [], 3),
        "A": (5, [], 3),
        "B": (5, [], 3)
    }
    workers6 = 3
    print("\n--- Example 6: Tie-breaking by Name ---")
    result_plan6 = plan_order(tasks6, workers6)
    # P=3 for all. D=5 for all. Tiebreaker: Alphabetical name (A, B, Z).
    print(f"Plan Order Result: {result_plan6}") 
    print(f"Critical Path: {critical_path(tasks6)}") # Expected: 5
    print(f"Makespan (W=3): {makespan(tasks6, workers6)}") # Expected: 5
