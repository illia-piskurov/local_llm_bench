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
    
    # Adjacency list: task -> tasks that depend on it
    dependents: dict[str, set[str]] = collections.defaultdict(set)
    # Initial dependency count for each task
    dependencies_remaining: dict[str, int] = {}
    
    for name in task_names:
        _, deps, _ = tasks[name]
        dependencies_remaining[name] = len(deps)
        for dep_name in deps:
            if dep_name not in task_names:
                # Handle case where dependency is listed but doesn't exist
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
    
    # Tracks tasks that are ready (dependencies met) but not yet started
    ready_queue: set[str] = {name for name in task_names if dependencies_remaining[name] == 0}
    
    # Tasks currently running: {task_name: finish_time}
    running_tasks: dict[str, int] = {}
    
    # Tracks tasks that have started (to prevent double-scheduling)
    started_tasks: set[str] = set()

    # --- 3. Main Simulation Loop ---

    while len(start_order) < N:
        
        # A. Determine Next Event Time (Time Advancement)
        if not running_tasks and ready_queue and len(start_order) == N:
            break # Should not happen if logic is correct, but safety break
        
        next_finish_time = float('inf')
        if running_tasks:
            next_finish_time = min(running_tasks.values())

        # If nothing is ready and nothing is running, we are stuck (should only happen if N=0)
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
                if dependent_task not in started_tasks: # Only update pending tasks
                    dependencies_remaining[dependent_task] -= 1
                    if dependencies_remaining[dependent_task] == 0:
                        ready_queue.add(dependent_task)

        # C. Scheduling Decision (At current_time)
        workers_available = workers - len(running_tasks)
        
        if workers_available > 0 and ready_queue:
            
            # Filter out tasks that have already started or are running
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
                # Re-sort the batch of starters using the official criteria
                def sort_key(task_name):
                    duration, _, priority = tasks[task_name]
                    return (-priority, duration, task_name)

                newly_started_names.sort(key=sort_key)
                start_order.extend(newly_started_names)


        # E. Cleanup Ready Queue (Tasks that start are no longer ready candidates)
        for task in tasks_to_start:
            ready_queue.discard(task)

    return start_order
