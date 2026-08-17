def max_depth(s: str) -> int:
    stack = []
    max_depth = 0
    
    for i, char in enumerate(s):
        if char == '(' or char == '[' or char == '{':
            stack.append(char)
            max_depth = max(max_depth, len(stack))
        elif char == ')' or char == ']' or char == '}':
            if not stack or stack.pop() != mapping[char]:
                return -1
    
    return max_depth

def find_unmatched(s: str) -> list[int]:
    stack = []
    unmatched_indices = []
    
    for i, char in enumerate(s):
        if char == '(' or char == '[' or char == '{':
            stack.append((char, i))
        elif char == ')' or char == ']' or char == '}':
            if not stack or stack.pop()[0] != mapping[char]:
                unmatched_indices.append(i)
    
    # Add remaining open brackets to unmatched indices
    for bracket, index in stack:
        unmatched_indices.append(index)
    
    return sorted(unmatched_indices)
