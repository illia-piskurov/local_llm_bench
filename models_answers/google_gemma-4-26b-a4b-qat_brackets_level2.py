def is_balanced(s: str) -> bool:
    """
    Проверяет, является ли строка сбалансированной по скобкам: (), [], {}.
    Игнорирует любые другие символы.
    """
    stack = []
    bracket_map = {')': '(', ']': '[', '}': '{'}
    opening_brackets = {'(', '[', '{'}

    for char in s:
        if char in opening_brackets:
            stack.append(char)
        elif char in bracket_map:
            if not stack or stack.pop() != bracket_map[char]:
                return False
    
    return not stack

def max_depth(s: str) -> int:
    """
    Возвращает максимальную глубину вложенности скобок.
    Глубина увеличивается при каждой открывающей скобке.
    Уменьшается только при корректном закрытии скобки.
    """
    stack = []
    bracket_map = {')': '(', ']': '[', '}': '{'}
    opening_brackets = {'(', '[', '{'}
    
    current_depth = 0
    max_d = 0
    
    for char in s:
        if char in opening_brackets:
            stack.append(char)
            current_depth += 1
            if current_depth > max_d:
                max_d = current_depth
        elif char in bracket_map:
            if stack and stack[-1] == bracket_map[char]:
                stack.pop()
                current_depth -= 1
            # Если не совпадает или стек пуст, глубина и стек не меняются
            
    return max_d

def find_unmatched(s: str) -> list[int]:
    """
    Возвращает отсортированный список индексов всех несовпавших скобок.
    """
    stack = []  # хранит кортежи (индекс, символ)
    bracket_map = {')': '(', ']': '[', '}': '{'}
    opening_brackets = {'(', '[', '{'}
    unmatched_closing = []

    for i, char in enumerate(s):
        if char in opening_brackets:
            stack.append((i, char))
        elif char in bracket_map:
            if stack and stack[-1][1] == bracket_map[char]:
                stack.pop()
            else:
                unmatched_closing.append(i)
    
    unmatched_opening = [item[0] for item in stack]
    return sorted(unmatched_closing + unmatched_opening)

if __name__ == "__main__":
    # Тесты для is_balanced
    assert is_balanced("([])") is True
    assert is_balanced("([)]") is False
    
    # Тесты для max_depth
    # "([)]" -> (idx 0: depth 1), ([ (idx 1: depth 2), ) (idx 2: mismatch, depth 2), ] (idx 3: match [, depth 1)
    assert max_depth("([)]") == 2
    assert max_depth("((()))") == 3
    assert max_depth("()[]{}") == 1
    assert max_depth("(((") == 3
    assert max_depth(")))") == 0
    
    # Тесты для find_unmatched
    # "([)]" -> (0, '(') не закрыта, (2, ')') не совпала с '['. Итог: [0, 2]
    assert find_unmatched("([)]") == [0, 2]
    # "())" -> (2, ')') лишняя. Итог: [2]
    assert find_unmatched("())") == [2]
    # "(()" -> (0, '(') не закрыта. Итог: [0]
    assert find_unmatched("(()") == [0]
    # "{[}]" -> (0, '{') не закрыта, (2, '}') не совпала с '['. Итог: [0, 2]
    assert find_unmatched("{[}]") == [0, 2]
    
    print("Все тесты пройдены!")
