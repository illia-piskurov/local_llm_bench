def is_balanced(s: str) -> bool:
    """
    Проверяет, является ли строка сбалансированной скобками.
    """
    stack = []
    mapping = {')': '(', ']': '[', '}': '{'}

    for char in s:
        if char in mapping:
            if stack and stack[-1] == mapping[char]:
                stack.pop()
            else:
                return False
        elif char in ['(', '[', '{']:
            stack.append(char)

    return not stack
