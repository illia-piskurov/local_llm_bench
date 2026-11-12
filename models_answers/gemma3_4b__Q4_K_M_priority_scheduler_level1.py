def plan_order(tasks: dict[str, tuple[int, list[str], int]], workers: int) -> list[str] | None:
    """
    Implements a task scheduler with dependencies, priorities, and a limited worker pool.
    """
    task_names = list(tasks.keys())
    ready_tasks = []
    running_tasks = []
    completed_tasks = []
    time = 0
    task_status = {task: "ready" for task in task_names}
    task_start_time = {task: -1 for task in task_names}

    while ready_tasks or running_tasks:
        # Add ready tasks to the running tasks
        for task_name in list(task_status):
            if task_status[task_name] == "ready":
                deps_met = all(dep in completed_tasks for dep in tasks[task_name][1])
                if deps_met:
                    ready_tasks.append((task_name, tasks[task_name][0], tasks[task_name][2]))
                    task_status[task_name] = "running"
                    task_start_time[task_name] = time

        # Sort running tasks based on priority, duration, and name
        running_tasks = sorted(running_tasks, key=lambda x: (x[2], x[1], x[0]))

        # Remove completed tasks
        completed_tasks = [task for task in running_tasks if task_status[task] != "running"]
        running_tasks = [task for task in running_tasks if task_status[task] == "running"]

        # Limit the number of running tasks
        num_running = len(running_tasks)
        if num_running > workers:
            running_tasks = running_tasks[:workers]

        # Advance time
        time += 1

        # Update task status
        for task_name in running_tasks:
            task_status[task_name] = "running"

        # Mark tasks as complete
        for task_name in running_tasks:
            if time - task_start_time[task_name] == tasks[task_name][0]:
                completed_tasks.append(task_name)
                task_status[task_name] = "completed"

    # Check for cyclic dependencies
    if any(task_status[task] != "completed" for task in task_names):
        return None

    return completed_tasks
