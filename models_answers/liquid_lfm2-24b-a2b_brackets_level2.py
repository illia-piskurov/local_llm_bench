def max_depth(s: str) -> int:
    depth = 0
    max_d = 0
    for char in s:
        if char in '([{':
            depth += 1
            if depth > max_d:
                max_d = depth
        elif char in ')]}':
            if not stack or matching[char] != stack[-1]:
                # не совпадает, не влияем на глубину и стек
                pass
            else:
                stack.pop()
                depth -= 1
    return max_d

def find_unmatched(s: str) -> list[int]:
    stack = []
    matching = {')': '(', ']': '[', '}': '{'}
    unmatched = set()
    for i, char in enumerate(s):
        if char in '([{':
            stack.append((char, i))
        elif char in ')]}':
            if not stack or stack[-1][0] != matching[char]:
                unmatched.add(i)
            else:
                stack.pop()
    unmatched.update(idx for _, idx in stack)
    return sorted(unmatched)

def is_balanced(s: str) -> bool:
    stack = []
    matching = {')': '(', ']': '[', '}': '{'}
    for char in s:
        if char in '([{':
            stack.append(char)
        elif char in ')]}':
            if not stack or stack[-1] != matching[char]:
                return False
            stack.pop()
    return not stack
