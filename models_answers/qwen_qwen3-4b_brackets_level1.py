def is_balanced(s: str) -> bool:
    stack = []
    closing = {')': '(', ']': '[', '}': '{'}
    for char in s:
        if char in '([{':
            stack.append(char)
        elif char in closing:
            if not stack:
                return False
            top = stack.pop()
            if closing[char] != top:
                return False
    return not stack
