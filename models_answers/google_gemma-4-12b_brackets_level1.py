def is_balanced(s: str) -> bool:
    stack = []
    mapping = {')': '(', ']': '[', '}': '{'}
    opening = "([{"
    closing = ")]}"

    for char in s:
        if char in opening:
            stack.append(char)
        elif char in closing:
            # If we find a closing bracket but the stack is empty, 
            # or it doesn't match the last opened bracket.
            if not stack or stack.pop() != mapping[char]:
                return False
    
    # If the stack is empty, all brackets were matched correctly.
    return len(stack) == 0
