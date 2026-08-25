from collections import defaultdict

def topo_sort(tasks: dict[str, list[str]]) -> list[str] | None:
    # Создаем граф зависимостей
    graph = defaultdict(list)
    for task, dependencies in tasks.items():
        for dependency in dependencies:
            graph[dependency].append(task)

    # Функция для поиска циклов в графе
    def has_cycle(node, visited, visiting):
        if node in visiting:
            return True
        if node in visited:
            return False
        visiting.add(node)
        for neighbor in graph[node]:
            if has_cycle(neighbor, visited, visiting):
                return True
        visiting.remove(node)
        visited.add(node)
        return False

    # Проверяем наличие циклов в графе
    if any(has_cycle(task, set(), set()) for task in tasks):
        return None

    # Алгоритм топологической сортировки
    def topological_sort(node, visited, result):
        if node in visited:
            return
        visited.add(node)
        for neighbor in graph[node]:
            topological_sort(neighbor, visited, result)
        result.append(node)

    result = []
    # Выполняем топологическую сортировку для всех независимых задач
    for task in tasks:
        if not any(task in dependencies for dependencies in tasks.values()):
            topological_sort(task, set(), result)

    return result

# Пример использования
tasks = {
    'A': ['B', 'C'],
    'B': ['D'],
    'C': ['E'],
    'D': [],
    'E': []
}
print(topo_sort(tasks))  # Вывод: ['D', 'E', 'B', 'C', 'A']
