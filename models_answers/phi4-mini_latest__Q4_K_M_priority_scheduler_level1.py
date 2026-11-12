from typing import List, Tuple, Dict, Optional
from heapq import heappush, heappop
from collections import defaultdict

def plan_order(tasks: Dict[str, Tuple[int, List[str], int]], workers: int) -> Optional[List[str]]:
    def can_execute(task, completed):
        return all(dep in completed for dep in task[1])

    def execute_task(task, time, completed, result):
        duration, deps, priority = task
        if can_execute(task, completed):
            result.append((time, task[0], priority))
            completed.add(task[0])
            for dep in deps:
                tasks[dep] = tasks[dep][:2] + (duration, deps, priority)
            tasks[dep] = tasks[dep][:1] + (duration, deps, priority)
            return time + duration
        return time

    def get_next_tasks(time, completed, available):
        tasks = {k: v for k, v in tasks.items() if k not in completed and (v[1] or can_execute(v, completed))}
        tasks = dict(sorted(tasks.items(), key=lambda item: (-item[1][2], item[1][0], item[0])))
        return [task for task in tasks.values() if task[1] and task[0] not in completed and task[0] not in available]

    completed = set()
    available = set()
    result = []
    tasks = {k: v for k, v in tasks.items()}
    available.update(tasks.keys())
    ready = get_next_tasks(0, completed, available)
    heap = [(priority, task[0], task[0]) for task in ready]
    heapq.heapify(heap)
    while ready or available:
        if ready:
            task = heappop(heap)
            next_time = execute_task(task, time, completed, result)
            if next_time > time:
                heappush(heap, (task[1], next_time, task[1]))
                ready = get_next_tasks(time, completed, available)
        else:
            while available:
                task = heappop(heap)
                next_time = execute_task(task, time, completed, result)
                if next_time > time:
                    heappush(heap, (task[1], next_time, task[1]))
                    ready = get_next_tasks(time, completed, available)
                else:
                    available.remove(task[2])
                    completed.add(task[2])
                    result.append((time, task[1], task[2]))
    return [task[1] for task in result]

# Example usage
tasks = {
    'A': (3, [], 2),
    'B': (2, ['A'], 1),
    'C': (1, ['B'], 3),
    'D': (2, ['C'], 2),
    'E': (1, ['A', 'B'], 4),
}
workers = 2
print(plan_order(tasks, workers))
