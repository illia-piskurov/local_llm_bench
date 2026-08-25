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
    mapping = {')': '(', ']': '[', '}': '{'}
    depth = 0
    max_d = 0
    
    for char in s:
        if char in mapping.values():
            stack.append(char)
            depth += 1
            if depth > max_d:
                max_d = depth
        elif char in mapping.keys():
            if stack and stack[-1] == mapping[char]:
                stack.pop()
                depth -= 1
    
    return max_d

def find_unmatched(s: str) -> list[int]:
    stack = []
    mapping = {')': '(', ']': '[', '}': '{'}
    unmatched_close = []
    
    for i, char in enumerate(s):
        if char in mapping.values():
            stack.append((i, char))
        elif char in mapping.keys():
            if not stack or stack[-1][1] != mapping[char]:
                unmatched_close.append(i)
            else:
                stack.pop()
    
    for i, _ in reversed(stack):
        unmatched_close.append(i)
    
    return sorted(unmatched_close)
