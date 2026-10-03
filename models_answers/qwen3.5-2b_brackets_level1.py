def is_balanced(s: str) -> bool:
    stack = []
    
    # Mapping from closing bracket to its corresponding opening bracket
    close_to_open = {')': '(', ']': '[', '}': '{'}
    
    for char in s:
        if char in close_to_open.values():
            # It's a closing bracket - check if it matches the top of stack
            if not stack or stack[-1] != close_to_open[char]:
                return False
            stack.pop()
        elif char in close_to_open.keys():
            # It's an opening bracket - push to stack
            stack.append(char)
    
    return len(stack) == 0
