from collections import defaultdict, deque
import heapq

def plan_order(tasks: dict[str, tuple[int, list[str], int]], workers: int) -> list[str] | None:
    def find_cycle():
        visited = set()
        recursion_stack = set()

        def dfs(node):
            if node in recursion_stack:
                return True
            if node in visited:
                return False

            visited.add(node)
            recursion_stack.add(node)

            for dep in tasks[node][1]:
                if dfs(dep):
                    return True

            recursion_stack.remove(node)
            return False

        for task in tasks.values():
            if dfs(task[0]):
                return True
        return False

    if find_cycle():
        return None

    # Sort tasks by priority, then duration, then name
    sorted_tasks = sorted(tasks.items(), key=lambda x: (-x[1][2], x[1][0], x[0]))

    # Initialize graph and in-degree for topological sort
    graph = defaultdict(list)
    in_degree = {task: 0 for task in tasks}

    for task, (duration, deps, _) in sorted_tasks:
        for dep in deps:
            graph[dep].append(task)
            in_degree[task] += 1

    # Queue for processing ready tasks
    ready_queue = []
    heapq.heapify(ready_queue)

    current_time = 0
    completed_tasks = set()

    while len(completed_tasks) < len(tasks):
        # Add all tasks that are ready (all dependencies completed) to the queue
        for task, duration in sorted_tasks:
            if in_degree[task] == 0 and task not in completed_tasks:
                heapq.heappush(ready_queue, (tasks[task][2], -duration, task))

        while ready_queue and len(completed_tasks) < len(tasks):
            _, duration, task = heapq.heappop(ready_queue)
            if current_time + duration <= workers:
                # Start the task
                completed_tasks.add(task)

                # Decrease in-degree for dependent tasks
                for dep in graph[task]:
                    in_degree[dep] -= 1

                # Update current time
                current_time += duration
            else:
                break

        if not ready_queue and len(completed_tasks) < len(tasks):
            return None  # Not enough workers to keep up with the tasks

    # Collect all completed tasks in order of their start time, priority, duration, name
    result = []
    for task in sorted(completed_tasks):
        result.append(task)

    return result
