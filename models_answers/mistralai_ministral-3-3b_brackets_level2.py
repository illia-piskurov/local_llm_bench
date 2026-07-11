def max_depth(s: str) -> int:
    stack = []
    current_depth = 0
    for char in s:
        if char in '([{':
            stack.append(char)
            current_depth += 1
        elif char in ')]}':
            if stack and stack[-1] == mapping[char]:
                stack.pop()
            else:
                current_depth -= 1
    return max(current_depth, len(stack))

def find_unmatched(s: str) -> list[int]:
    stack = []
    unmatched_indices = []
    mapping = {')': '(', ']': '[', '}': '{'}
    reverse_mapping = {v: k for k, v in mapping.items()}
    open_symbols = set(reverse_mapping.values())
    close_symbols = set(mapping.keys())

    for idx, char in enumerate(s):
        if char in open_symbols:
            stack.append(idx)
        elif char in close_symbols:
            if not stack or stack[-1] != reverse_mapping[char]:
                unmatched_indices.append(idx)
            else:
                stack.pop()

    unmatched_open = [idx for idx in stack]
    return sorted(unmatched_indices + unmatched_open)

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
