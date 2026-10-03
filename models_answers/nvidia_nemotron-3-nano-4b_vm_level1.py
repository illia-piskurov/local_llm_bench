def run(program: str) -> list[str]:
    lines = program.splitlines()
    stack = []
    output = []

    for idx, line in enumerate(lines, start=1):
        line = line.strip()
        if not line or line.startswith('#'):
            continue

        tokens = line.split()
        op = tokens[0]

        if op == 'PUSH':
            n = int(tokens[1])
            stack.append(n)

        elif op == 'POP':
            if not stack:
                raise ValueError(f"Line {idx}: POP on empty stack")
            stack.pop()

        elif op == 'ADD':
            if len(stack) < 2:
                raise ValueError(f"Line {idx}: ADD requires two values, got {len(stack)}")
            b = stack.pop()
            a = stack.pop()
            stack.append(a + b)

        elif op == 'SUB':
            if len(stack) < 2:
                raise ValueError(f"Line {idx}: SUB requires two values, got {len(stack)}")
            b = stack.pop()
            a = stack.pop()
            stack.append(a - b)

        elif op == 'MUL':
            if len(stack) < 2:
                raise ValueError(f"Line {idx}: MUL requires two values, got {len(stack)}")
            b = stack.pop()
            a = stack.pop()
            stack.append(a * b)

        elif op == 'DIV':
            if len(stack) < 2:
                raise ValueError(f"Line {idx}: DIV requires two values, got {len(stack)}")
            b = stack.pop()
            a = stack.pop()
            if b == 0:
                raise ValueError(f"Line {idx}: division by zero")
            stack.append(a // b)

        elif op == 'DUP':
            if not stack:
                raise ValueError(f"Line {idx}: DUP on empty stack")
            stack.append(stack[-1])

        elif op == 'SWAP':
            if len(stack) < 2:
                raise ValueError(f"Line {idx}: SWAP requires two values, got {len(stack)}")
            a = stack.pop()
            b = stack.pop()
            stack.append(a)
            stack.append(b)

        elif op == 'PRINT':
            if not stack:
                raise ValueError(f"Line {idx}: PRINT on empty stack")
            output.append(str(stack[-1]))

        else:
            raise ValueError(f"Line {idx}: unknown instruction '{op}'")

    return output
