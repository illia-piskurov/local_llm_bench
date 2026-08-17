from typing import Dict, List, Tuple

def plan_order(tasks: Dict[str, Tuple[int, List[str], int]], workers: int) -> List[str] | None:
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

    # Sort tasks by priority, duration, and name
    sorted_tasks = sorted(tasks.keys(), key=lambda x: (-tasks[x][2], tasks[x][0], x))

    # Topological sort to get the order of execution
    topological_sort(graph, indegree, [])

    return topological_sort(graph, indegree, [])
