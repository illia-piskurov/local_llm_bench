def is_balanced(s: str) -> bool:
    """Check if brackets in the string are balanced."""
    pairs = {')': '(', ']': '[', '}': '{'}
    open_brackets = set(pairs.values())
    stack = []

    for ch in s:
        if ch in open_brackets:
            stack.append(ch)
        elif ch in pairs:
            if not stack or stack[-1] != pairs[ch]:
                return False
            stack.pop()

    return not stack
