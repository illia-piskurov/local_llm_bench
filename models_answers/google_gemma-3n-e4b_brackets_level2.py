def is_balanced(s: str) -> bool:
    """
    Проверяет сбалансированность скобок в строке.

    Args:
        s: Строка для проверки.

    Returns:
        True, если строка сбалансирована, False - в противном случае.
    """
    stack = []
    mapping = {")": "(", "]": "[", "}": "{"}

    for char in s:
        if char in mapping:
            top_element = stack.pop() if stack else '#'  # Use '#' as a placeholder for empty stack
            if mapping[char] != top_element:
                return False
        elif char in "([{":
            stack.append(char)

    return not stack

def max_depth(s: str) -> int:
    """
    Вычисляет максимальную глубину вложенности скобок.

    Args:
        s: Строка для анализа.

    Returns:
        Максимальная глубина вложенности.
    """
    max_depth = 0
    current_depth = 0
    for char in s:
        if char in "([{":
            current_depth += 1
            max_depth = max(max_depth, current_depth)
        elif char in ")]}":
            if current_depth > 0:
                current_depth -= 1
    return max_depth

def find_unmatched(s: str) -> list[int]:
    """
    Находит индексы несовпавших скобок.

    Args:
        s: Строка для анализа.

    Returns:
        Отсортированный по возрастанию список индексов несовпавших скобок.
    """
    stack = []
    unmatched = []
    mapping = {")": "(", "]": "[", "}": "{"}
    for i, char in enumerate(s):
        if char in "([{":
            stack.append((char, i))
        elif char in ")]}":
            if stack:
                top_char, top_index = stack.pop()
                if mapping[char] != top_char:
                    unmatched.append(top_index)
                    unmatched.append(i)
            else:
                unmatched.append(i)

    for char, index in stack:
        unmatched.append(index)

    return sorted(list(set(unmatched)))
