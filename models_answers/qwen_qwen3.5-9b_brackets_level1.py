def is_balanced(s: str) -> bool:
    stack = []
    pairs = {')': '(', ']': '[', '}': '{'}
    opening = set(pairs.values())
    closing = set(pairs.keys())

    for char in s:
        if char in opening:
            stack.append(char)
        elif char in closing:
            if not stack:
                return False
            top = stack.pop()
            if pairs[char] != top:
                return False
    return len(stack) == 0

if __name__ == "__main__":
    test_cases = [
        ("()", True),
        ("([])", True),
        ("([)]", False),
        ("(]", False),
        ("", True),
        ("a(b)c", True),
        ("(((", False),
        (")))", False),
    ]
    for s, expected in test_cases:
        result = is_balanced(s)
        print(f"Input: {s}, Expected: {expected}, Got: {result}, Pass: {result == expected}")
