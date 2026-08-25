def is_balanced(s: str) -> bool:
    stack = []
    closing = {')': '(', ']': '[', '}': '{'}
    for char in s:
        if char in '([{':
            stack.append(char)
        elif char in closing:
            if not stack:
                return False
            top = stack.pop()
            if closing[char] != top:
                return False
    return not stack

def max_depth(s: str) -> int:
    stack = []
    current_depth = 0
    max_depth_val = 0
    closing = {')': '(', ']': '[', '}': '{'}
    for c in s:
        if c in '([{':
            stack.append(c)
            current_depth += 1
            if current_depth > max_depth_val:
                max_depth_val = current_depth
        else:
            if stack and closing[c] == stack[-1]:
                stack.pop()
                current_depth -= 1
    return max_depth_val

def find_unmatched(s: str) -> list[int]:
    unmatched = []
    stack = []  # stores (char, index)
    closing = {')': '(', ']': '[', '}': '{'}
    for i, c in enumerate(s):
        if c in '([{':
            stack.append((c, i))
        else:
            if stack:
                top_char, top_index = stack[-1]
                if closing[c] == top_char:
                    stack.pop()
                else:
                    unmatched.append(i)
    # collect remaining opening brackets
    unmatched += [index for (char, index) in stack]
    return sorted(unmatched)
