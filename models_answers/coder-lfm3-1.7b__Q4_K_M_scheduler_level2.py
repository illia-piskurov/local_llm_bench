from collections import defaultdict, deque
from typing import Dict, List, Optional


def topo_sort(tasks: dict[str, list[str]]) -> List[str]:
    """Return a topological ordering of `tasks` or None if a cycle exists."""
    adj = defaultdict(list)          # outgoing edges (dependency → dependent)
    indeg = {node: 0 for node in tasks}   # incoming edge counts

    # Build adjacency & indegree
    for task, deps in tasks.items():
        for dep in deps:
            adj[dep].append(task)
            indeg[task] += 1

    # Kahn's algorithm
    queue = deque([node for node, deg in indeg.items() if deg == 0])
    result = []
    while queue:
        u = queue.popleft()
        result.append(u)
        for v in adj[u]:
            indeg[v] -= 1
            if indeg[v] == 0:
                queue.append(v)

    # Cycle detection: not all nodes were processed?
    if len(result) != len(tasks):
        return None
    return result


def critical_path(tasks: dict[str, tuple[int, list[str]]]) -> Optional[int]:
    """
    Return the length of the longest weighted path (critical path) in the dependency graph.
    
    Parameters:
    - tasks: mapping task name → (duration, dependencies_list)
    
    Returns:
        int | None
            The maximum total duration along any directed path respecting dependencies,
            or None if the dependency graph contains a cycle.
    """
    # Build adjacency list and indegree counters
    adj = defaultdict(list)               # edge from dependency to dependent
    indeg = {node: 0 for node in tasks}
    durations = {}

    # Also ensure every task appears as a key even if it has no outgoing edges
    for task, (dur, _deps) in tasks.items():
        durations[task] = dur

    # Add reverse direction edges to track successors (outgoing)
    for task, (_, deps) in tasks.items():
        for dep in deps:
            adj[dep].append(task)          # edge from dependency → dependent
            indeg[task] += 1                # increase indegree of the dependent

    # Kahn's algorithm to obtain topological order and detect cycles
    queue = deque([node for node, deg in indeg.items() if indeg[node] == 0])
    topo_order = []
    while queue:
        u = queue.popleft()
        topo_order.append(u)
        for v in adj[u]:
            indeg[v] -= 1
            if indeg[v] == 0:
                queue.append(v)

    # If a cycle exists, some nodes remain with non‑zero indegree → not all processed
    if len(topo_order) != len(tasks):
        return None

    # Dynamic programming on the topological order to find longest weighted path.
    dp = {node: 0 for node in tasks}   # longest total duration ending at each task
    max_path = 0

    for u in topo_order:
        dur = durations.get(u, 0)
        if dur > 0:
            dp[u] = dur
        else:
            dp[u] = 0
        
        for v in adj[u]:
            # When we traverse an edge from u → v (u is a prerequisite of v),
            # the path ending at v can be extended by adding duration of v.
            candidate = dp[u] + durations.get(v, 0)
            if candidate > dp[v]:
                dp[v] = candidate

    return max(dp.values())
