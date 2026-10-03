def is_balanced(s: str) -> bool:
    filtered = [c for c in s if c in '({[]})']
    if not filtered:
        return False
    stack = []
    closing_to_opening = {')': '(', ']': '[', '}': '{'}
    for char in filtered:
        if char in closing_to_opening:
            if not stack:
                return False
            popped = stack.pop()
            if closing_to_opening[char] != popped:
                return False
        else:
            stack.append(char)
    return not stack

def max_depth(s: str) -> int:
    current_depth = 0
    max_depth = 0
    stack = []
    closing_to_opening = {')': '(', ']': '[', '}': '{'}
    for char in s:
        if char in '({[]})':
            if char in '({[':
                stack.append(char)
                current_depth += 1
                if current_depth > max_depth:
                    max_depth = current_depth
            else:
                if stack and stack[-1] == closing_to_opening[char]:
                    stack.pop()
                    current_depth -= 1
    return max_depth

def find_unmatched(s: str) -> list[int]:
    stack = []
    unmatched_open = []
    closing_unmatched = []
    closing_to_opening = {')': '(', ']': '[', '}': '{'}
    for i, char in enumerate(s):
        if char in '({[]})':
            if char in '({[':
                stack.append(char)
            else:
                if stack and stack[-1] == closing_to_opening[char]:
                    stack.pop()
                else:
                    closing_unmatched.append(i)
    return sorted(closing_unmatched + unmatched_open)
