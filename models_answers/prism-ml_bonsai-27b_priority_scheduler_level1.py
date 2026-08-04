import heapq

def plan_order(tasks: dict[str, tuple[int, list[str], int]], workers: int) -> list[str] | None:
    adj = {name: [] for name in tasks}
    in_degree = {}
    for name, (dur, deps, pri) in tasks.items():
        in_degree[name] = len(deps)
        for dep in deps:
            if dep not in adj:
                adj[dep] = []
            adj[dep].append(name)

    ready_queue = []
    for name, (dur, deps, pri) in tasks.items():
        if in_degree[name] == 0:
            heapq.heappush(ready_queue, (-pri, dur, name))

    active_tasks = []  # min-heap of (finish_time, task_name)
    order = []
    completed_count = 0
    current_time = 0

    while ready_queue or active_tasks:
        if len(active_tasks) < workers and ready_queue:
            neg_pri, dur, name = heapq.heappop(ready_queue)
            finish_time = current_time + dur
            heapq.heappush(active_tasks, (finish_time, name))
            order.append(name)
            completed_count += 1

        elif active_tasks:
            finish_time, finished_name = heapq.heappop(active_tasks)
            current_time = max(current_time, finish_time)
            for dependent in adj[finished_name]:
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    dur, _, pri = tasks[dependent]
                    heapq.heappush(ready_queue, (-pri, dur, dependent))

        else:
            break

    return order if completed_count == len(tasks) else None
