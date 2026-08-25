def max_depth(s: str) -> int:
    stack = []
    depth = 0
    for i, char in enumerate(s):
        if char in '{[(':
            stack.append((char, i))
            depth += 1
        elif char in ')}]':
            if not stack or (stack[-1][0] != '(' and stack[-1][0] != '[' and stack[-1][0] != '{') or \
               (stack[-1][0] == '(' and char != ')') or (stack[-1][0] == '[' and char != ']') or \
               (stack[-1][0] == '{' and char != '}'):
                continue
            else:
                stack.pop()
                depth -= 1
    return depth

def find_unmatched(s: str) -> list[int]:
    stack = []
    unmatched = []

    for i, char in enumerate(s):
        if char in '{[':
            stack.append((char, i))
        elif char in ')}':
            if not stack or (stack[-1][0] != '(' and stack[-1][0] != '[' and stack[-1][0] != '{') or \
               (stack[-1][0] == '(' and char != ')') or (stack[-1][0] == '[' and char != ']') or \
               (stack[-1][0] == '{' and char != '}'):
                unmatched.append(i)
            else:
                stack.pop()

    return sorted([u for s, u in stack if s == '(' or s == '[' or s == '{'] + unmatched)
