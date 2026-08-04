def is_balanced(s: str) -> bool:
    stack = []
    opening_scopes = {'(', '{', '['}
    closing_scopes = {')': '(', '}': '{', ']': '['}
    
    for char in s:
        if char in opening_scopes:
            stack.append(char)
        elif char in closing_scopes:
            if not stack or stack.pop() != closing_scopes[char]:
                return False
    return not stack

def max_depth(s: str) -> int:
    max_depth = 0
    current_depth = 0
    for char in s:
        if char in opening_scopes:
            current_depth += 1
            if current_depth > max_depth:
                max_depth = current_depth
        else:
            current_depth -= 1
    return max_depth

def find_unmatched(s: str) -> list[int]:
    stack = []
    unmatched_indices = []
    for i, char in enumerate(s):
        if char in opening_scopes:
            stack.append(i)
        elif char in closing_scopes:
            if stack and s[stack[-1]] in opening_scopes:
                stack.pop()
            else:
                unmatched_indices.append(i)
    return sorted(unmatched_indices)
