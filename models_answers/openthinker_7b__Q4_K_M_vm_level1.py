def run(program: str) -> list[str]:
    stack = []
    output = []
    lines = program.split('\n')
    line_number = 1
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            line_number += 1
            continue
        parts = stripped.split()
        cmd = parts[0]
        args = parts[1:]
        if cmd == 'PUSH':
            if len(args) != 1:
                raise ValueError(f"Invalid arguments for PUSH on line {line_number}")
            try:
                n = int(args[0])
            except ValueError:
                raise ValueError(f"Invalid number for PUSH on line {line_number}")
            stack.append(n)
        elif cmd == 'POP':
            if not stack:
                raise ValueError(f"Stack underflow on line {line_number}")
            stack.pop()
        elif cmd == 'ADD':
            if len(stack) < 2:
                raise ValueError(f"Not enough values for ADD on line {line_number}")
            a = stack.pop()
            b = stack.pop()
            stack.append(a + b)
        elif cmd == 'SUB':
            if len(stack) < 2:
                raise ValueError(f"Not enough values for SUB on line {line_number}")
            b = stack.pop()
            a = stack.pop()
            stack.append(a - b)
        elif cmd == 'MUL':
            if len(stack) < 2:
                raise ValueError(f"Not enough values for MUL on line {line_number}")
            a = stack.pop()
            b = stack.pop()
            stack.append(a * b)
        elif cmd == 'DIV':
            if len(stack) < 2:
                raise ValueError(f"Not enough values for DIV on line {line_number}")
            b = stack.pop()
            if b == 0:
                raise ValueError(f"Division by zero on line {line_number}")
            a = stack.pop()
            stack.append(a // b)
        elif cmd == 'DUP':
            if not stack:
                raise ValueError(f"Stack underflow for DUP on line {line_number}")
            stack.append(stack[-1])
        elif cmd == 'SWAP':
            if len(stack) < 2:
                raise ValueError(f"Not enough values for SWAP on line {line_number}")
            a = stack.pop()
            b = stack.pop()
            stack.append(a)
            stack.append(b)
        elif cmd == 'PRINT':
            if not stack:
                raise ValueError(f"Stack underflow for PRINT on line {line_number}")
            output.append(str(stack[-1]))
        else:
            raise ValueError(f"Unknown command {cmd} on line {line_number}")
        line_number += 1
    return output
