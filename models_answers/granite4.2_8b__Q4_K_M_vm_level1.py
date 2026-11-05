def run(program: str) -> list[str]:
    lines = program.splitlines()
    stack = []
    output = []

    for idx, raw in enumerate(lines, 1):
        line = raw.strip()
        if not line or line.startswith('#'):
            continue
        parts = line.split()
        cmd = parts[0]

        if cmd == 'PUSH':
            try:
                n = int(parts[1])
            except (IndexError, ValueError):
                raise RuntimeError(f"Line {idx}: PUSH requires an integer argument") from None
            stack.append(n)

        elif cmd == 'POP':
            if not stack:
                raise RuntimeError(f"Line {idx}: POP on empty stack") from None
            stack.pop()

        elif cmd == 'ADD':
            if len(stack) < 2:
                raise RuntimeError(f"Line {idx}: ADD needs two values") from None
            b = stack.pop()
            a = stack.pop()
            stack.append(a + b)

        elif cmd == 'SUB':
            if len(stack) < 2:
                raise RuntimeError(f"Line {idx}: SUB needs two values") from None
            b = stack.pop()
            a = stack.pop()
            stack.append(a - b)

        elif cmd == 'MUL':
            if len(stack) < 2:
                raise RuntimeError(f"Line {idx}: MUL needs two values") from None
            b = stack.pop()
            a = stack.pop()
            stack.append(a * b)

        elif cmd == 'DIV':
            if len(stack) < 2:
                raise RuntimeError(f"Line {idx}: DIV needs two values") from None
            b = stack.pop()
            a = stack.pop()
            if b == 0:
                raise RuntimeError(f"Line {idx}: Division by zero") from None
            # integer division, floor for negative? use //
            stack.append(a // b)

        elif cmd == 'DUP':
            if not stack:
                raise RuntimeError(f"Line {idx}: DUP on empty stack") from None
            stack.append(stack[-1])

        elif cmd == 'SWAP':
            if len(stack) < 2:
                raise RuntimeError(f"Line {idx}: SWAP needs at least two values") from None
            a = stack[-2]
            b = stack[-1]
            stack[-2] = b
            stack[-1] = a

        elif cmd == 'PRINT':
            if not stack:
                raise RuntimeError(f"Line {idx}: PRINT on empty stack") from None
            val = stack[-1]
            # convert to string without extra formatting
            output.append(str(val))

        else:
            raise RuntimeError(f"Line {idx}: Unknown instruction '{cmd}'") from None

    return output
