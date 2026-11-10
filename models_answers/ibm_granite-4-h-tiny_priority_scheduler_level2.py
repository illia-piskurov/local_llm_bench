from collections import defaultdict

def critical_path(tasks: dict[str, tuple[int, list[str], int]]) -> int | None:
    graph = defaultdict(list)
    indegree = {task: 0 for task in tasks}
    
    for task, (_, deps, _) in tasks.items():
        for dep in deps:
            graph[dep].append(task)
            indegree[task] += 1
            
    def dfs(node):
        if node in visited:
            return float('inf')
        visited.add(node)
        max_path = 0
        for neighbor in graph[node]:
            max_path = max(max_path, dfs(neighbor))
        visited.remove(node)
        return max_path + tasks[node][0]
    
    visited = set()
    longest_path = 0
    
    for task in tasks:
        if indegree[task] == 0:  # Start from tasks with no dependencies
            longest_path = max(longest_path, dfs(task))
    
    return longest_path if len(visited) == len(tasks) else None

def makespan(tasks: dict[str, tuple[int, list[str], int]], workers: int) -> int | None:
    schedule = plan_order(tasks, workers)
    if schedule is None:
        return None
    return max(start_time for start_time, _ in schedule)
