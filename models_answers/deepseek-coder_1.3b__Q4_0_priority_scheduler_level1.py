import threading
import heapq

class TaskScheduler:
    def __init__(self, tasks: dict[str, tuple[int, list[str], int]], workers: int):
        self.tasks = tasks
        self.workers = workers
        self.results = []
        self.available_workers = list(range(workers))
        self.lock = threading.Lock()

    def plan_order(self):
        # Create a priority queue for tasks
        self.tasks = {k: (v[0], v[1], v[2]) for k, v in self.tasks.items()}
        self.tasks = [(-v[2], v[0], v[1]) for v in self.tasks.values()]
        heapq.heapify(self.tasks)

        # Create a list for results
        self.results = []

        # Run tasks
        while self.tasks or self.available_workers:
            self.execute_tasks()

        # Check for cyclic dependencies
        for task in self.tasks:
            if self.has_cycle(task[1]):
                return None

        return self.results

    def execute_tasks(self):
        while self.tasks and self.available_workers:
            task = heapq.heappop(self.tasks)
            worker = self.available_workers.pop(0)

            self.lock.acquire()
            self.results.append(task[1])
            self.lock.release()

            self.available_workers.append(worker)

    def has_cycle(self, deps: list[str]) -> bool:
        visited = set()
        stack = deps

        while stack:
            dep = stack.pop()

            if dep in visited:
                return True

            visited.add(dep)
            stack.extend(self.tasks[dep][1])

        return False
