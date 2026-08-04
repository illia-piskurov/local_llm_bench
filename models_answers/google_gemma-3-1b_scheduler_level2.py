def critical_path(tasks: dict[str, tuple[int, list[str]]]) -> int | None:
    """
    Реализует расчёт критического пути в графе зависимостей.

    Args:
        tasks: Словарь, где значение — кортеж (длительность_задачи, список_зависимостей).

    Returns:
        Длина критического пути - суммарная длительность самой долгой цепочки зависимых друг от друга задач.
        Если в графе есть цикл — верни None.
    """
    visited = set()
    recursion_stack = []
    max_length = 0

    def dfs(task):
        if task in visited:
            return 0

        visited.add(task)
        for dependent_task in tasks[task][1]:
            length = dfs(dependent_task)
            max_length = max(max_length, length + 1)

        recursion_stack.append(task)
        visited.remove(task)
        for dependent_task in tasks[task][1]:
            length = dfs(dependent_task)
            max_length = max(max_length, length + 1)

        recursion_stack.pop()

    for task in tasks:
        if task not in visited:
            dfs(task)

    return max_length
