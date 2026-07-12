def is_balanced(s: str) -> bool:
    stack = []
    mapping = {')': '(', ']': '[', '}': '{'}
    
    for char in s:
        if char == '(' or char == '[' or char == '{':
            stack.append(char)
        elif char in mapping:
            if not stack or stack[-1] != mapping[char]:
                return False
            stack.pop()
    
    return len(stack) == 0

if __name__ == "__main__":
    test_cases = [
        ("", True),
        ("()", True),
        (")(", False),
        ("([])", True),
        ("([)]", False),
        ("(]", False),
        ("{[]}", True)
    ]
    
    for s, expected in test_cases:
        result = is_balanced(s)
        print(f"Test case '{s}': Expected {expected}, got {result}")
