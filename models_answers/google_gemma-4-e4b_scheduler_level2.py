from collections import deque, defaultdict
import math

def topo_sort(tasks: dict[str, list[str]]) -> list[str] | None:
    """
    Performs a topological sort on the given task dependency graph.

    Args:
        tasks: A dictionary where key is the task name and value is 
               a list of prerequisite task names.

    Returns:
        A list of tasks in a valid execution order, or None if a cycle exists.
    """
    
    # 1. Initialize structures
    in_degree = {}
    adj = defaultdict(list)
    all_tasks = set()

    # Collect all unique task names (both keys and dependencies)
    for task, deps in tasks.items():
        all_tasks.add(task)
        for dep in deps:
            all_tasks.add(dep)

    # Initialize in-degrees for all known tasks to 0
    for task in all_tasks:
        in_degree[task] = 0

    # 2. Build the graph (adj list) and calculate initial in-degrees
    for task, deps in tasks.items():
        current_in_degree = len(deps)
        in_degree[task] = current_in_degree
        
        for dep in deps:
            # Edge goes from dependency -> dependent task
            adj[dep].append(task)

    # 3. Initialize queue with tasks having no dependencies (in-degree 0)
    queue = deque([task for task in all_tasks if in_degree[task] == 0])
    result = []

    # 4. Process using Kahn's algorithm
    while queue:
        task = queue.popleft()
        result.append(task)

        # For every task that depends on the current 'task'
        for neighbor in adj[task]:
            # Decrement its dependency count
            in_degree[neighbor] -= 1
            
            # If all dependencies are met, enqueue the neighbor
            if in_degree[neighbor] == 0:
                queue.append(neighbor)

    # 5. Check for cycles
    if len(result) != len(all_tasks):
        return None  # Cycle detected
    else:
        return result


def critical_path(tasks: dict[str, tuple[int, list[str]]]) -> int | None:
    """
    Calculates the length of the critical path (longest duration) through 
    the task dependency graph using CPM principles.

    Args:
        tasks: A dictionary where key is the task name and value is a 
               tuple (duration, list_of_dependencies).

    Returns:
        The total duration of the longest dependent sequence, or None if a cycle exists.
    """
    
    # --- Initialization ---
    in_degree = {}
    adj = defaultdict(list)
    all_tasks = set()
    durations = {}
    
    for task, data in tasks.items():
        duration, _ = data
        durations[task] = duration
        all_tasks.add(task)

    # Collect all unique task names (including dependencies that might not be keys)
    for _, (_, deps) in tasks.items():
        for dep in deps:
            all_tasks.add(dep)

    # Initialize structures for all known tasks
    for task in all_tasks:
        in_degree[task] = 0
        
    # ES (Earliest Start Time): Tracks the earliest time a task can begin.
    earliest_start_time = {task: 0 for task in all_tasks}

    # 1. Build graph and calculate initial in-degrees
    for task, data in tasks.items():
        _, deps = data
        current_in_degree = len(deps)
        in_degree[task] = current_in_degree
        
        for dep in deps:
            # Edge goes from dependency -> dependent task
            adj[dep].append(task)

    # 2. Initialize queue with tasks having no dependencies (in-degree 0)
    queue = deque([task for task in all_tasks if in_degree[task] == 0])
    processed_count = 0
    max_project_duration = 0

    # 3. Process using Kahn's algorithm and calculate path lengths
    while queue:
        P = queue.popleft()
        processed_count += 1
        
        # If P is not a defined task (i.e., it was only listed as a dependency), 
        # we assume its duration is 0 for calculation purposes, unless explicitly given.
        duration_p = durations.get(P, 0)

        # Calculate Earliest Finish Time (EF) for P
        ef_p = earliest_start_time[P] + duration_p
        
        # Update the overall maximum project duration found so far
        max_project_duration = max(max_project_duration, ef_p)

        # For every task N that depends on P
        for N in adj[P]:
            # Update ES for N: N cannot start until P finishes. 
            # We take the maximum required start time from all dependencies.
            earliest_start_time[N] = max(earliest_start_time[N], ef_p)
            
            # Decrement dependency count
            in_degree[N] -= 1
            
            # If all dependencies are met, enqueue N
            if in_degree[N] == 0:
                queue.append(N)

    # 4. Check for cycles and return result
    if processed_count != len(all_tasks):
        return None  # Cycle detected
    else:
        return max_project_duration

if __name__ == '__main__':
    # --- Testing topo_sort (Included for completeness) ---
    print("--- Topo Sort Tests ---")
    tasks1 = {
        "B": ["A"],
        "C": ["A"],
        "D": ["B", "C"]
    }
    result1 = topo_sort(tasks1)
    print(f"Example 1 Result: {result1}")

    tasks3 = {
        "B": ["A"],
        "A": ["B"]
    }
    result3 = topo_sort(tasks3)
    print(f"Example 3 Result (Cycle): {result3}")


    # --- Testing Critical Path ---
    print("\n--- Critical Path Tests ---")

    # Example 1: Simple linear path A -> B -> C. Durations: A=2, B=3, C=4. CP = 9.
    tasks_cp1 = {
        "B": (3, ["A"]),
        "C": (4, ["B"])
    }
    cp1 = critical_path(tasks_cp1)
    print(f"Example 1 (Linear Path): CP = {cp1}") # Expected: 9

    # Example 2: Parallel paths meeting at D. A->D (Duration 5), B->D (Duration 3). Durations: A=2, B=4, D=1.
    # Max path is A -> D (2 + 1 = 3) or B -> D (4 + 1 = 5). CP = 5.
    tasks_cp2 = {
        "D": (1, ["A", "B"]),
        "A": (2, []),
        "B": (4, [])
    }
    cp2 = critical_path(tasks_cp2)
    print(f"Example 2 (Parallel Paths): CP = {cp2}") # Expected: 5

    # Example 3: Cycle detection. A -> B, B -> A. Durations: A=1, B=1.
    tasks_cp3 = {
        "B": (1, ["A"]),
        "A": (1, ["B"])
    }
    cp3 = critical_path(tasks_cp3)
    print(f"Example 3 (Cycle): CP = {cp3}") # Expected: None

    # Example 4: Complex graph. A=5, B=2, C=3. D depends on A and B. E depends on C.
    # Path 1: A -> D (5 + 1) = 6
    # Path 2: B -> D (2 + 1) = 3
    # Max path to D is 6. Then D -> F (duration 4). Total max path: 6 + 4 = 10.
    tasks_cp4 = {
        "D": (1, ["A", "B"]),
        "F": (4, ["D"]),
        "E": (3, []) # Independent task E
    }
    # We must ensure all tasks are accounted for in the dependency list or keys. 
    # Let's add A and B explicitly as independent start nodes.
    tasks_cp4_full = {
        "A": (5, []),
        "B": (2, []),
        "E": (3, []),
        "D": (1, ["A", "B"]),
        "F": (4, ["D"])
    }
    cp4 = critical_path(tasks_cp4_full)
    print(f"Example 4 (Complex Graph): CP = {cp4}") # Expected: 10
