def is_balanced(s: str) -> bool:
    brackets = [c for c in s if c in "({[]})"]
    if not brackets:
        return True
    stack = []
    for b in brackets:
        if b in "({[":
            stack.append(b)
        else:
            if not stack:
                return False
            top = stack.pop()
            if (b == ')' and top != '(') or (b == ']' and top != '[') or (b == '}' and top != '{'):
                return False
    return len(stack) == 0
