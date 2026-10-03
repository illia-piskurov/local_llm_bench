import collections
from typing import List, Dict, Tuple, Optional

def plan_order(tasks: dict[str, tuple[int, list[str], int]], workers: int) -> Optional[list[str]]:
    """
    Schedules tasks with dependencies, priorities, and limited worker pool.

    Args:
        tasks: Dictionary mapping task name to (duration, deps, priority).
        workers: Maximum number of concurrent workers.

    Returns:
        List[str] of tasks in the order they start, or None if a cycle exists.
    """
    task_names = list(tasks.keys())
    N = len(task_names)

    # --- 1. Dependency Graph Setup and Cycle Detection ---
    
    dependents: dict[str, set[str]] = collections.defaultdict(set)
    dependencies_remaining: dict[str, int] = {}
    
    for name in task_names:
        _, deps, _ = tasks[name]
        dependencies_remaining[name] = len(deps)
        for dep_name in deps:
            if dep_name not in task_names:
                # Dependency listed but doesn't exist
                return None 
            dependents[dep_name].add(name)

    # Cycle Detection using DFS (State: 0=Unvisited, 1=Visiting, 2=Visited)
    state = {name: 0 for name in task_names}
    def has_cycle(node):
        if state[node] == 1:  # Currently visiting -> Cycle detected
            return True
        if state[node] == 2: # Already visited
            return False

        state[node] = 1  # Mark as Visiting
        _, deps, _ = tasks[node]
        for dep in deps:
            if has_cycle(dep):
                return True
        
        state[node] = 2  # Mark as Visited
        return False

    for name in task_names:
        if state[name] == 0 and has_cycle(name):
            return None # Cycle detected

    # --- 2. Simulation Setup ---

    current_time = 0
    start_order: list[str] = []
    
    ready_queue: set[str] = {name for name in task_names if dependencies_remaining[name] == 0}
    running_tasks: dict[str, int] = {} # {task_name: finish_time}
    started_tasks: set[str] = set()

    # --- 3. Main Simulation Loop ---

    while len(start_order) < N:
        
        # A. Determine Next Event Time (Time Advancement)
        next_finish_time = float('inf')
        if running_tasks:
            next_finish_time = min(running_tasks.values())

        # If nothing is ready and nothing is running, we are done or stuck
        if not running_tasks and not ready_queue and len(start_order) < N:
             break 

        # Advance time to the next event (completion or start opportunity)
        if running_tasks and next_finish_time != float('inf'):
            current_time = next_finish_time
        elif ready_queue and not running_tasks:
            # If nothing is running, but tasks are ready, we schedule immediately at current_time
            pass 

        # B. Process Completions (At current_time)
        finished_this_step = []
        for task_name, finish_time in list(running_tasks.items()):
            if finish_time <= current_time:
                finished_this_step.append(task_name)

        for finished_task in finished_this_step:
            del running_tasks[finished_task]
            
            # Update dependencies for all tasks that depended on this one
            for dependent_task in dependents[finished_task]:
                if dependent_task not in started_tasks: 
                    dependencies_remaining[dependent_task] -= 1
                    if dependencies_remaining[dependent_task] == 0:
                        ready_queue.add(dependent_task)

        # C. Scheduling Decision (At current_time)
        workers_available = workers - len(running_tasks)
        
        if workers_available > 0 and ready_queue:
            candidates = [t for t in ready_queue if t not in started_tasks]

            if candidates:
                # Sorting criteria (Tie-breakers):
                # 1. Highest Priority (Max) -> Use negative priority for ascending sort
                # 2. Shortest Duration (Min)
                # 3. Alphabetical Name (Ascending)
                def sort_key(task_name):
                    duration, _, priority = tasks[task_name]
                    return (-priority, duration, task_name)

                candidates.sort(key=sort_key)
                tasks_to_start = candidates[:workers_available]
            else:
                tasks_to_start = []


        # D. Execute Starts and Update State
        if tasks_to_start:
            newly_started_names = []
            for task_name in tasks_to_start:
                duration, _, _ = tasks[task_name]
                finish_time = current_time + duration
                
                running_tasks[task_name] = finish_time
                started_tasks.add(task_name)
                newly_started_names.append(task_name)

            # The output list must reflect the tie-breaking order for tasks starting at the same time
            if newly_started_names:
                def sort_key(task_name):
                    duration, _, priority = tasks[task_name]
                    return (-priority, duration, task_name)

                newly_started_names.sort(key=sort_key)
                start_order.extend(newly_started_names)


        # E. Cleanup Ready Queue (Tasks that start are no longer ready candidates)
        for task in tasks_to_start:
            ready_queue.discard(task)

    return start_order

def critical_path(tasks: dict[str, tuple[int, list[str], int]]) -> Optional[int]:
    """
    Calculates the length of the longest dependency path (critical path).
    Returns None if a cycle exists.
    """
    task_names = list(tasks.keys())
    
    # --- 1. Cycle Detection (Reused from plan_order) ---
    dependents: dict[str, set[str]] = collections.defaultdict(set)
    state = {name: 0 for name in task_names} # 0=Unvisited, 1=Visiting, 2=Visited

    def has_cycle(node):
        if state[node] == 1: return True
        if state[node] == 2: return False

        state[node] = 1
        _, deps, _ = tasks[node]
        for dep in deps:
            if dep not in task_names: continue # Ignore external dependencies if they aren't defined tasks
            if has_cycle(dep):
                return True
        
        state[node] = 2
        return False

    for name in task_names:
        if state[name] == 0 and has_cycle(name):
            return None # Cycle detected

    # --- 2. Critical Path Calculation using Memoized DFS ---
    
    # memo[task_name] stores the length of the longest path ending at task_name
    memo: dict[str, int] = {}

    def calculate_longest_path(task_name):
        if task_name in memo:
            return memo[task_name]

        _, deps, _ = tasks[task_name]
        
        max_predecessor_path = 0
        for dep in deps:
            # We assume cycle detection passed, so recursive calls will terminate.
            if dep in task_names:
                max_predecessor_path = max(max_predecessor_path, calculate_longest_path(dep))

        # Path length = Duration of current task + Max path leading to it
        duration = tasks[task_name][0]
        result = duration + max_predecessor_path
        memo[task_name] = result
        return result

    max_critical_path = 0
    for name in task_names:
        max_critical_path = max(max_critical_path, calculate_longest_path(name))
        
    return max_critical_path


def makespan(tasks: dict[str, tuple[int, list[str], int]], workers: int) -> Optional[int]:
    """
    Calculates the total completion time (makespan) of all tasks using limited workers.
    Returns None if a cycle exists.
    """
    task_names = list(tasks.keys())
    N = len(task_names)

    # --- 1. Dependency Graph Setup and Cycle Detection (Reused) ---
    dependents: dict[str, set[str]] = collections.defaultdict(set)
    dependencies_remaining: dict[str, int] = {}
    
    for name in task_names:
        _, deps, _ = tasks[name]
        dependencies_remaining[name] = len(deps)
        for dep_name in deps:
            if dep_name not in task_names: return None 
            dependents[dep_name].add(name)

    state = {name: 0 for name in task_names}
    def has_cycle(node):
        if state[node] == 1: return True
        if state[node] == 2: return False

        state[node] = 1
        _, deps, _ = tasks[node]
        for dep in deps:
            if dep not in task_names: continue
            if has_cycle(dep): return True
        
        state[node] = 2
        return False

    for name in task_names:
        if state[name] == 0 and has_cycle(name):
            return None # Cycle detected

    # --- 2. Simulation Setup (Similar to plan_order) ---

    current_time = 0
    started_tasks: set[str] = set()
    ready_queue: set[str] = {name for name in task_names if dependencies_remaining[name] == 0}
    running_tasks: dict[str, int] = {} # {task_name: finish_time}

    # --- 3. Main Simulation Loop ---

    while len(started_tasks) < N or running_tasks:
        
        # A. Determine Next Event Time (Time Advancement)
        next_finish_time = float('inf')
        if running_tasks:
            next_finish_time = min(running_tasks.values())

        # If nothing is ready and nothing is running, we are done or stuck
        if not running_tasks and not ready_queue and len(started_tasks) < N:
             break 

        # Advance time to the next event (completion or start opportunity)
        if running_tasks and next_finish_time != float('inf'):
            current_time = next_finish_time
        elif ready_queue and not running_tasks:
            pass # Schedule immediately at current_time

        # B. Process Completions (At current_time)
        finished_this_step = []
        for task_name, finish_time in list(running_tasks.items()):
            if finish_time <= current_time:
                finished_this_step.append(task_name)

        for finished_task in finished_this_step:
            del running_tasks[finished_task]
            
            # Update dependencies for all tasks that depended on this one
            for dependent_task in dependents[finished_task]:
                if dependent_task not in started_tasks: 
                    dependencies_remaining[dependent_task] -= 1
                    if dependencies_remaining[dependent_task] == 0:
                        ready_queue.add(dependent_task)

        # C. Scheduling Decision (At current_time)
        workers_available = workers - len(running_tasks)
        
        if workers_available > 0 and ready_queue:
            candidates = [t for t in ready_queue if t not in started_tasks]

            if candidates:
                # Sorting criteria (Tie-breakers):
                def sort_key(task_name):
                    duration, _, priority = tasks[task_name]
                    return (-priority, duration, task_name)

                candidates.sort(key=sort_key)
                tasks_to_start = candidates[:workers_available]
            else:
                tasks_to_start = []


        # D. Execute Starts and Update State
        if tasks_to_start:
            for task_name in tasks_to_start:
                duration, _, _ = tasks[task_name]
                finish_time = current_time + duration
                
                running_tasks[task_name] = finish_time
                started_tasks.add(task_name)

        # E. Cleanup Ready Queue 
        for task in tasks_to_start:
            ready_queue.discard(task)

    # The makespan is the time when the last running task finishes.
    if not running_tasks and len(started_tasks) == N:
        return current_time
    elif running_tasks:
        return max(running_tasks.values())
    else:
        # Case for zero tasks
        return 0 if N == 0 else None
