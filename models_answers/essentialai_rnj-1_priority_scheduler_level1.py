def plan_order(tasks: dict[str, tuple[int, list[str], int]], workers: int) -> list[str] | None:
    from collections import defaultdict, deque

    def has_cycle():
        visited = set()
        rec_stack = set()

        def dfs(task):
            if task in rec_stack:
                return True
            if task in visited:
                return False
            visited.add(task)
            rec_stack.add(task)
            for dep in tasks[task][1]:
                if dfs(dep):
                    return True
            rec_stack.remove(task)
            return False

        for task in tasks:
            if dfs(task):
                return None
        return True

    def topological_sort():
        indegree = {task: 0 for task in tasks}
        graph = defaultdict(list)

        for task, (_, deps, _) in tasks.items():
            for dep in deps:
                graph[dep].append(task)
                indegree[task] += 1

        queue = deque([task for task in tasks if indegree[task] == 0])
        sorted_tasks = []

        while queue:
            queue = deque(sorted(queue, key=lambda x: (-tasks[x][2], tasks[x][0], x)))
            current_task = queue.popleft()
            sorted_tasks.append(current_task)
            for neighbor in graph[current_task]:
                indegree[neighbor] -= 1
                if indegree[neighbor] == 0:
                    queue.append(neighbor)

        return sorted_tasks

    def schedule(tasks, workers):
        task_times = defaultdict(int)
        scheduled = []
        available_workers = workers

        while tasks:
            ready_tasks = [task for task in tasks if all(task_times[dep] > 0 for dep in tasks[task][1])]
            ready_tasks.sort(key=lambda x: (-tasks[x][2], tasks[x][0], x))
            
            scheduled_batch = []
            for _ in range(min(available_workers, len(ready_tasks))):
                task = ready_tasks.pop()
                scheduled_batch.append(task)
                available_workers -= 1
                duration = tasks[task][0]
                start_time = max((task_times[dep] for dep in tasks[task][1]), default=0)
                end_time = start_time + duration
                task_times[task] = end_time

            scheduled.extend(scheduled_batch)
            available_workers += len(scheduled_batch)

        return [task for _, task in sorted((task_times[task], task) for task in tasks)]

    if not has_cycle():
        sorted_tasks = topological_sort()
        return schedule(sorted_tasks, workers)
    else:
        return None
