def max_depth(s: str) -> int:
    stack = []
    max_depth = 0
    
    for char in s:
        if char in '([{':
            stack.append(char)
            max_depth = max(max_depth, len(stack))
        elif char in ')]}':
            if not stack or stack[-1] != matching_bracket[char]:
                continue
            stack.pop()
    
    return max_depth

def find_unmatched(s: str) -> list[int]:
    stack = []
    unmatched_indices = []
    matching_bracket = {')': '(', ']': '[', '}': '{'}
    
    for i, char in enumerate(s):
        if char in '([{':
            stack.append((char, i))
        elif char in ')]}':
            if not stack or stack[-1][0] != matching_bracket[char]:
                unmatched_indices.append(i)
            else:
                stack.pop()
    
    unmatched_indices.extend(i for _, i in stack)
    return sorted(unmatched_indices)

matching_bracket = {')': '(', ']': '[', '}': '{'}
