def is_balanced(s: str) -> bool:
    stack = []
    opening_brackets = {'(', '[', '{'}
    closing_to_opening = {')': '(', ']': '[', '}': '{'}
    
    for char in s:
        if char in opening_brackets:
            stack.append(char)
        elif char in closing_to_opening:
            if not stack or stack.pop() != closing_to_opening[char]:
                return False
    
    return len(stack) == 0

def max_depth(s: str) -> int:
    stack = []
    opening_brackets = {'(', '[', '{'}
    closing_to_opening = {')': '(', ']': '[', '}': '{'}
    
    current_depth = 0
    max_depth_val = 0
    
    for char in s:
        if char in opening_brackets:
            stack.append(char)
            current_depth += 1
            if current_depth > max_depth_val:
                max_depth_val = current_depth
        elif char in closing_to_opening:
            expected = closing_to_opening[char]
            if stack and stack[-1] == expected:
                stack.pop()
                current_depth -= 1
    
    return max_depth_val

def find_unmatched(s: str) -> list[int]:
    stack = [] # Stores (char, index)
    opening_brackets = {'(', '[', '{'}
    closing_to_opening = {')': '(', ']': '[', '}': '{'}
    
    unmatched_indices = []
    
    for i, char in enumerate(s):
        if char in opening_brackets:
            stack.append((char, i))
        elif char in closing_to_opening:
            expected = closing_to_opening[char]
            if not stack or stack[-1][0] != expected:
                unmatched_indices.append(i)
            else:
                stack.pop()
    
    # Add remaining opening brackets indices
    for _, idx in stack:
        unmatched_indices.append(idx)
        
    return sorted(unmatched_indices)

if __name__ == "__main__":
    print(is_balanced("()"))          # True
    print(max_depth("()"))            # 1
    print(find_unmatched(")("))       # [0, 1]
    print(is_balanced("([])"))       # True
    print(max_depth("([])"))          # 2
    print(find_unmatched("([)]"))     # [0, 2]
