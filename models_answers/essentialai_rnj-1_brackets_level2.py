def max_depth(s: str) -> int:
    stack = []
    max_d = 0
    
    for char in s:
        if char in "([{":
            stack.append(char)
            max_d = max(max_d, len(stack))
        elif char in ")]}":
            if not stack or (char == ')' and stack[-1] != '(') or \
               (char == ']' and stack[-1] != '[') or \
               (char == '}' and stack[-1] != '{'):
                continue
            else:
                stack.pop()
    
    return max_d


def find_unmatched(s: str) -> list[int]:
    stack = []
    unmatched_indices = []
    
    for i, char in enumerate(s):
        if char in "([{":
            stack.append((char, i))
        elif char in ")]}":
            if not stack or (char == ')' and stack[-1][0] != '(') or \
               (char == ']' and stack[-1][0] != '[') or \
               (char == '}' and stack[-1][0] != '{'):
                unmatched_indices.append(i)
            else:
                stack.pop()
    
    # Add indices of any remaining open brackets
    for _, idx in stack:
        unmatched_indices.append(idx)
    
    return sorted(unmatched_indices)
