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
                # Handle case where dependency is listed but not defined
                return None # Or raise an error, assuming valid input structure
            adj[dep].append(task_name)
            in_degree[task_name] += 1

    # Kahn's algorithm for cycle detection (Topological Sort check)
    queue = collections.deque([task for task in tasks if in_degree[task] == 0])
    processed_count = 0
    temp_topo_order = []
    
    temp_in_degree = dict(in_degree) # Use a copy for the check
    q_check = collections.deque([task for task in tasks if temp_in_degree[task] == 0])

    while q_check:
        u = q_check.popleft()
        temp_topo_order.append(u)
        processed_count += 1
        
        for v in adj[u]:
            temp_in_degree[v] -= 1
            if temp_in_degree[v] == 0:
                q_check.append(v)

    if processed_count != len(tasks):
        return None # Cycle detected

    # --- 2. Simulation Setup ---
    
    # State tracking
    completed_tasks = set()
    running_tasks: Dict[str, int] = {}  # {task_name: finish_time}
    scheduled_order: List[str] = []
    current_time = 0

    # Tasks whose dependencies are met but haven't started yet.
    eligible_tasks = set(task for task in tasks if not tasks[task][1]) # Start with tasks having no deps
    
    # Keep track of which tasks still need to be scheduled/completed
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
                        # Check if all dependencies of the successor are now met
                        _, deps, _ = tasks[successor]
                        if all(dep in completed_tasks for dep in deps):
                            eligible_tasks.add(successor)

        elif eligible_tasks and not running_tasks:
            # Edge case: If nothing is running but we have ready tasks (T=0 start)
            pass # Time remains 0, scheduling happens below

        # --- B. Scheduling Phase ---
        
        available_workers = workers - len(running_tasks)
        if available_workers <= 0 and not running_tasks:
             # Should only happen if workers is 0 and there are tasks to run
            break 

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
                # The order of starting tasks must follow the tie-breaker rule
                scheduled_order.extend(tasks_to_start) 
                
                for task_name in tasks_to_start:
                    duration, _, _ = tasks[task_name]
                    finish_time = current_time + duration
                    running_tasks[task_name] = finish_time
                    eligible_tasks.remove(task_name)

        # --- C. Termination Check ---
        if not running_tasks and not eligible_tasks and remaining_tasks:
            # We are stuck (e.g., dependencies form a cycle that wasn't caught, or workers=0)
            break 

    return scheduled_order if len(completed_tasks) == len(tasks) else None

if __name__ == '__main__':
    # Example 1: Basic sequential execution
    tasks1 = {
        "A": (5, [], 1),
        "B": (3, ["A"], 2),
        "C": (2, ["B"], 3)
    }
    workers1 = 1
    print("--- Example 1 (Sequential) ---")
    result1 = plan_order(tasks1, workers1)
    # Expected: ['A', 'B', 'C']
    print(f"Result 1: {result1}")

    # Example 2: Parallel execution with limited workers
    tasks2 = {
        "T1": (5, [], 1),
        "T2": (3, [], 2),
        "T3": (7, ["T1"], 3)
    }
    workers2 = 2
    print("\n--- Example 2 (Parallel, Workers=2) ---")
    result2 = plan_order(tasks2, workers2)
    # T1 and T2 start at t=0. T2 has higher priority/shorter duration tie-breaker than T1? No, Prio: T2(2), T1(1). 
    # Order: T2 (P=2), T1 (P=1).
    # Expected Start Order: ['T2', 'T1']
    print(f"Result 2: {result2}")

    # Example 3: Complex scheduling and tie-breaking
    tasks3 = {
        "A": (5, [], 1),  # P=1, D=5
        "B": (2, [], 2),  # P=2, D=2 -> Should start first
        "C": (4, ["B"], 3) # Must wait for B
    }
    workers3 = 2
    print("\n--- Example 3 (Tie-breaking & Dependencies) ---")
    result3 = plan_order(tasks3, workers3)
    # T=0: Candidates A, B. Select B (P=2), then A (P=1). Start order: ['B', 'A']
    print(f"Result 3: {result3}")

    # Example 4: Cycle detection
    tasks4 = {
        "X": (1, ["Y"], 1),
        "Y": (1, ["Z"], 1),
        "Z": (1, ["X"], 1)
    }
    workers4 = 3
    print("\n--- Example 4 (Cycle Detection) ---")
    result4 = plan_order(tasks4, workers4)
    # Expected: None
    print(f"Result 4: {result4}")

    # Example 5: Workers limit forcing sequential start
    tasks5 = {
        "A": (10, [], 3),
        "B": (10, [], 2),
        "C": (10, [], 1)
    }
    workers5 = 1
    print("\n--- Example 5 (Workers Limit=1) ---")
    result5 = plan_order(tasks5, workers5)
    # Order: A (P=3), B (P=2), C (P=1). All start sequentially.
    print(f"Result 5: {result5}")

    # Example 6: Multiple tasks ready at T=0 with same priority/duration
    tasks6 = {
        "Z": (5, [], 3),
        "A": (5, [], 3),
        "B": (5, [], 3)
    }
    workers6 = 3
    print("\n--- Example 6 (Tie-breaking by Name) ---")
    result6 = plan_order(tasks6, workers6)
    # P=3 for all. D=5 for all. Tiebreaker: Alphabetical name (A, B, Z).
    # Expected Start Order: ['A', 'B', 'Z']
    print(f"Result 6: {result6}")
