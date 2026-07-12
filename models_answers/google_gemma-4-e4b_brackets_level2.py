def is_balanced(s: str) -> bool:
    """
    Проверяет сбалансированность скобок (), [], {} в строке s.
    Игнорирует все символы, кроме скобок.
    """
    stack = []
    mapping = {")": "(", "]": "[", "}": "{"}
    open_brackets = set(["(", "[", "{"])

    for char in s:
        # 1. Если это закрывающая скобка
        if char in mapping:
            # Проверяем, что стек не пуст и что вершина стека соответствует ожидающему открывающему типу
            top_element = stack.pop() if stack else '#' # Используем заглушку для проверки пустоты
            
            if top_element != mapping[char]:
                return False
        
        # 2. Если это открывающая скобка
        elif char in open_brackets:
            stack.append(char)
        
        # 3. Иначе - игнорируем символ

    # После прохода по всей строке, стек должен быть пустым для сбалансированности
    return not stack

def max_depth(s: str) -> int:
    """
    Возвращает максимальную глубину вложенности скобок при сканировании строки слева направо.
    """
    stack = []
    max_d = 0
    current_depth = 0
    mapping = {")": "(", "]": "[", "}": "{"}
    open_brackets = set(["(", "[", "{"])

    for char in s:
        if char in open_brackets:
            stack.append(char)
            current_depth += 1
            max_d = max(max_d, current_depth)
        elif char in mapping:
            # Проверка на корректное закрытие
            top_element = stack[-1] if stack else None
            if top_element == mapping[char]:
                stack.pop()
                current_depth -= 1
            # Если не совпадает или стек пуст, ничего не происходит с глубиной/стеком

    return max_d

def find_unmatched(s: str) -> list[int]:
    """
    Возвращает отсортированный список индексов всех "несовпавших" скобок.
    """
    stack = []  # Хранит кортежи (символ, индекс)
    unmatched_indices = set()
    mapping = {")": "(", "]": "[", "}": "{"}
    open_brackets = set(["(", "[", "{"])

    for i, char in enumerate(s):
        if char in open_brackets:
            # Открывающая скобка: сохраняем символ и его индекс
            stack.append((char, i))
        elif char in mapping:
            # Закрывающая скобка
            top_element = stack[-1] if stack else None
            expected_open = mapping[char]

            if top_element and top_element[0] == expected_open:
                # Совпадение: удаляем пару со стека
                stack.pop()
            else:
                # Несовпадение (или стек пуст): эта закрывающая скобка непарна
                unmatched_indices.add(i)

    # После прохода, все оставшиеся индексы в стеке — это незакрытые открывающие скобки
    for _, index in stack:
        unmatched_indices.add(index)

    return sorted(list(unmatched_indices))
