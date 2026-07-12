```python
from collections import deque, defaultdict


def topo_sort(tasks: dict[str, list[str]]) -> list[str] | None:
    # 1. Identify all unique tasks (nodes) in the graph.
    # Nodes can be keys in 'tasks' or appear only as dependencies in values.
    all_nodes = set(tasks.keys())
    for deps in tasks.values():
        all_nodes.update(deps)
    
    # 2. Build adjacency list and calculate in-degrees.
    # Edge direction: dependency -> dependent (since tasks[dependent] lists dependencies).
    adj = defaultdict(list)
    in_degree = {node: 0 for node in all_nodes}
    
    for task, deps in tasks.items():
        for dep in deps:
            adj[dep].append(task)
            in_degree[task] += 1
            
    # 3. Initialize queue with nodes having zero in-degree.
    queue = deque([node for node in all_nodes if in_degree[node] == 0])
    
    result = []
    
    # 4.
