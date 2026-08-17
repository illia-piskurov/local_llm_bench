def critical_path(tasks: dict[str, tuple[int, list[str], int]]) -> int | None:
    from collections import defaultdict

    def detect_cycle(graph):
        visited = set()
        stack = set()
        for node in graph:
            if not visited:
                if dfs(node, visited, stack, graph):
                    return True
        return False

    def dfs(node, visited, stack, graph):
        visited.add(node)
        stack.add(node)
        for neighbor in graph[node][1]:
            if neighbor not in visited:
                if dfs(neighbor, visited, stack, graph):
                    return True
            elif neighbor in stack:
                return True
        stack.remove(node)
        return False

    graph = defaultdict(list)
    for task, (duration, deps, _) in tasks.items():
        for dep in deps:
            graph[dep].append(task)
    if detect_cycle(graph):
        return None

    nodes = list(graph.keys())
    durations = [tasks[task][0] for task in tasks]
    priorities = [-p for _, _, _, _ in tasks.values()]
    names = [task for _, _, _, task in tasks.items()]
    nodes.sort(key=lambda x: (-priorities.index(tasks[x][3]), durations.index(tasks[x][0]), names.index(x)))
    return max(durations)

def makespan(tasks: dict[str, tuple[int, list[str], int]], workers: int) -> int | None:
    from heapq import heappush, heappop

    def has_cycle(task, visited, stack):
        if task in stack:
            return True
        if task in visited:
            return False
        visited.add(task)
        stack.add(task)
        for dep in tasks[task][1]:
            if has_cycle(dep, visited, stack):
                return True
        stack.remove(task)
        return False

    tasks_with_priority = [(priority, duration, deps, task) for task, (duration, deps, priority) in tasks.items()]
    tasks_with_order = sorted(tasks_with_priority, key=lambda x: (-x[0], x[1], x[2]))

    if has_cycle(tasks_with_priority[0][2]):
        return None

    completed = set()
    ready_queue = []
    order = []

    for priority, duration, deps, task in tasks_with_priority:
        if all(dep in completed for dep in deps) and len(ready_queue) < workers:
            if not ready_queue or (priority > -ready_queue[0][0]) or \
               (priority == -ready_queue[0][0] and duration < -ready_queue[0][1]) or \
               (priority == -ready_queue[0][0] and duration == -ready_queue[0][1]):
                ready_queue.append((priority, duration, deps, task))
            completed.add(task)
            order.append(task)

    while ready_queue:
        priority, duration, deps, task = heappop(ready_queue)
        order.append(task)
        for dep in tasks[task][1]:
            if dep not in completed:
                completed.add(dep)
                heappush(ready_queue, (priority, duration, deps, tasks[dep][2]))

    critical_length = critical_path(tasks_with_order)
    if critical_length is None:
        return makespan(tasks, workers)

    durations = [tasks[task][0] for task in order]
    total_duration = sum(durations)
    return total_duration
