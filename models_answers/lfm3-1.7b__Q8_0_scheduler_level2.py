from collections import deque
from typing import Dict, List, Set, Union

def topo_sort(tasks: Dict[str, List[str]]) -> List[str] | None:
    # Collect all task names (keys and any dependencies that appear as values)
    nodes: Set[str] = set(tasks.keys())
    for deps in tasks.values():
        nodes.update(deps)

    # Initialize adjacency list (outgoing edges) and indegree for each node
    adj: Dict[str, List[str]] = {node: [] for node in nodes}
    indegree: Dict[str, int] = {node: 0 for node in nodes}

    # Build graph from dependency lists:
    # For each task t with dependencies dep_list,
    # add an edge from each dependency d to t.
    for t, dep_list in tasks.items():
        for d in dep_list:
            adj[d].append(t)
            indegree[t] += 1

    # Kahn's algorithm
    queue = deque([node for node in nodes if indegree[node] == 0])
    result: List[str] = []

    while queue:
        u = queue.popleft()
        result.append(u)
        for v in adj[u]:
            indegree[v] -= 1
            if indegree[v] == 0:
                queue.append(v)

    # If we processed all nodes, the graph is a DAG; otherwise there was a cycle.
    if len(result) != len(nodes):
        return None

    return result


def critical_path(tasks: Dict[str, tuple[int, list[str]]]) -> int | None:
    """
    tasks: dict where each value is (duration:int, dependencies_list:list[str])
    
    Returns the length of the longest path (critical path) i.e., maximum total duration
    along any chain of dependent tasks. If there is a cycle in the dependency graph,
    return None.
    """
    # Collect all task names and their durations / dependency lists
    nodes: Set[str] = set()
    for t, entry in tasks.items():
        nodes.add(t)
        if len(entry) >= 2:
            deps = entry[1]
            nodes.update(deps)

    adj = {node: [] for node in nodes}
    indegree: Dict[str, int] = {node: 0 for node in nodes}
    duration_map: Dict[str, int] = {}

    # Build graph and count indegrees
    for t, (dur, dep_list) in tasks.items():
        duration_map[t] = dur
        for d in dep_list:
            adj[d].append(t)
            indegree[t] += 1

    # Kahn's algorithm to obtain a topological order
    queue: deque = deque([node for node in nodes if indegree[node] == 0])
    topo_order: List[str] = []

    while queue:
        u = queue.popleft()
        topo_order.append(u)
        for v in adj[u]:
            indegree[v] -= 1
            if indegree[v] == 0:
                queue.append(v)

    # Cycle detection: if not all nodes processed, graph contains a cycle
    if len(topo_order) != len(nodes):
        return None

    # Compute the longest path (finish time) for each node in topological order.
    finish_time = {node: 0 for node in nodes}
    for u in topo_order:
        # predecessors are those that have edges into u? We need max over dependencies of u,
        # but we stored outgoing adjacency. However, to compute longest path ending at u,
        # we can look at its own duration plus the maximum finish among its dependencies.
        # In our graph, adj[d] contains tasks that depend on d (i.e., edges from dependency -> dependent).
        # Therefore for node u, its predecessors are not directly listed in adj. 
        # We need to know which nodes have an edge to u. Since we built adjacency from dependency->dependent,
        # the incoming list is missing. But we can infer: For each task t, its dependencies are given.
        # So we can compute predecessor max using duration_map and dep_list.
        pass

    # Simpler: Recompute longest path by iterating over nodes in topological order
    # using their dependency lists (from tasks). Since topo_order respects dependencies,
    # all predecessors appear earlier, so we have their finish_time already.

    for t in topo_order:
        deps = tasks[t][1]  # but careful: tasks is the original dict? It's overwritten.
        # We need the dependency list for this task. Since we only modified tasks dict,
        # we can store dependencies separately earlier, or reconstruct from input.
        # To avoid complexity, let's recompute using duration_map and nodes' own dep lists:
    # However, to keep it simple and correct, we will iterate over the original mapping of
    # (duration, deps). Since critical_path receives a different dict type,
    # we can't easily get dependencies. Let's rebuild from tasks values directly.

    # Actually easier: Use the earlier adjacency to compute max predecessor finish.
    # We can store for each node its list of dependencies as dep_list_from_tasks = [
    #   ...], but we don't have them stored. Let's just re-derive:
    
    # Rebuild dependency lists from tasks entries (the second element)
    # Since critical_path only has the dict, we could extract deps by iterating values.
    pass
