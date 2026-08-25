from typing import Dict, List, Tuple

def critical_path(tasks: Dict[str, Tuple[int, List[str], int]]) -> int | None:
    def find_cycle(graph):
        visited = set()
        rec_stack = set()

        def dfs(node):
            if node in rec_stack:
                return True
            if node in visited:
                return False

            visited.add(node)
            rec_stack.add(node)

            for neighbor in graph[node]:
                if dfs(neighbor):
                    return True

            rec_stack.remove(node)
            return False

        for node in tasks:
            if find_cycle({node: tasks[node][1]}):
                return None
        return None

    def topological_sort(graph, indegree, order):
        queue = [node for node in graph if indegree[node] == 0]
        while queue:
            node = queue.pop(0)
            order.append(node)

            for neighbor in graph[node]:
                indegree[neighbor] -= 1
                if indegree[neighbor] == 0:
                    queue.append(neighbor)

    # Check for cycles
    cycle = find_cycle(tasks)
    if cycle is not None:
        return None

    # Build the graph and calculate indegrees
    graph = {}
    indegree = {}

    for task, (duration, deps, priority) in tasks.items():
        graph[task] = deps
        indegree[task] = len(deps)

    # Sort tasks by duration, then by name
    sorted_tasks = sorted(tasks.keys(), key=lambda x: (tasks[x][0], x))

    # Topological sort to get the order of execution
    topological_sort(graph, indegree, [])

    # Calculate the critical path length
    critical_path_length = 0
    current_time = 0

    for task in sorted_tasks:
        duration = tasks[task][0]
        current_time += duration
        critical_path_length = max(critical_path_length, current_time)

    return critical_path_length


def makespan(tasks: Dict[str, Tuple[int, List[str], int]], workers: int) -> int | None:
    def find_cycle(graph):
        visited = set()
        rec_stack = set()

        def dfs(node):
            if node in rec_stack:
                return True
            if node in visited:
                return False

            visited.add(node)
            rec_stack.add(node)

            for neighbor in graph[node]:
                if dfs(neighbor):
                    return True

            rec_stack.remove(node)
            return False

        for node in tasks:
            if find_cycle({node: tasks[node][1]}):
                return None
        return None

    def topological_sort(graph, indegree, order):
        queue = [node for node in graph if indegree[node] == 0]
        while queue:
            node = queue.pop(0)
            order.append(node)

            for neighbor in graph[node]:
                indegree[neighbor] -= 1
                if indegree[neighbor] == 0:
                    queue.append(neighbor)

    # Check for cycles
    cycle = find_cycle(tasks)
    if cycle is not None:
        return None

    # Build the graph and calculate indegrees
    graph = {}
    indegree = {}

    for task, (duration, deps, priority) in tasks.items():
        graph[task] = deps
        indegree[task] = len(deps)

    # Sort tasks by priority, duration, then by name
    sorted_tasks = sorted(tasks.keys(), key=lambda x: (-tasks[x][2], tasks[x][0], x))

    # Topological sort to get the order of execution
    topological_sort(graph, indegree, [])

    # Calculate the makespan
    current_time = 0
    max_workers = workers

    for task in sorted_tasks:
        duration = tasks[task][0]
        if len(sorted_tasks) - sorted_tasks.index(task) <= max_workers:
            max_workers -= 1
        current_time += duration

    return current_time
