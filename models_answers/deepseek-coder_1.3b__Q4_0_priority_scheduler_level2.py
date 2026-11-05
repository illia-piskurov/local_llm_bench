import threading
import heapq

class TaskScheduler:
    def  __init__(self, tasks: dict[str, tuple[int, list[str], int]], workers: int):
        self.tasks = tasks
        self.workers = workers
        self.results = []
        self.available_workers = list(range(workers))
        self.lock = threading.Lock()

    def plan_order(self):
        self.tasks = {k: (v[0], v[1], v[2]) for k, v in self.tasks.items()}
        self.tasks = [(-v[2], v[0], v[1]) for v in self.tasks.values()]
        heapq.heapify(self.tasks)

        self.results = []

        while self.tasks or self.available_workers:
            self.execute_tasks()

        for task in self.tasks:
            if self.has_cycle(task[1][1:]):
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

    def critical_path(self, tasks: dict[str, tuple[int, list[str], int]]) -> int | None:
        self.tasks = tasks
        self.results = []

        while self.tasks or self.available_workers:
            self.execute_tasks()

        for task in self.tasks:
            if self.has_cycle(task[1][1:]):
                return None

        return max(task[0] for task in self.results)

    def makespan(self, tasks: dict[str, tuple[int, list[str], int]], workers: int) -> int | None:
        self.tasks = tasks
        self.workers = workers
        self.results = []

        while self.tasks or self.available_workers:
            self.execute_tasks()

        for task in self.tasks:
            if self.has_cycle(task[1][1:]):
                return None

        return max(task[0] for task in self.results)
