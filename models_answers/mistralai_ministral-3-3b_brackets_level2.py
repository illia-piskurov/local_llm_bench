def is_balanced(s: str) -> bool:
    stack = []
    mapping = {')': '(', ']': '[', '}': '{'}
    for char in s:
        if char in mapping.values():
            stack.append(char)
        elif char in mapping.keys():
            if not stack or stack.pop() != mapping[char]:
                return False
    return len(stack) == 0

def max_depth(s: str) -> int:
    stack = []
    current_depth = 0
    for char in s:
        if char in {'(', '[', '{'}:
            stack.append(char)
            current_depth += 1
        elif char in {')', ']', '}'}:
            if stack and stack[-1] == mapping[char]:
                stack.pop()
                current_depth -= 1
    return max(current_depth, 0)

def find_unmatched(s: str) -> list[int]:
    stack = []
    unmatched_indices = set()
    mapping = {')': '(', ']': '[', '}': '{'}

    for idx, char in enumerate(s):
        if char in mapping.values():
            stack.append((char, idx))
        elif char in mapping.keys():
            if not stack or stack[-1][0] != mapping[char]:
                unmatched_indices.add(idx)
            else:
                stack.pop()

    for (char, idx) in stack:
        unmatched_indices.add(idx)

    return sorted(unmatched_indices)
