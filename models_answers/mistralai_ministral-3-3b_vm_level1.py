def run(program: str) -> list[str]:
    stack = []
    output = []
    lines = program.split('\n')
    for line_num, line in enumerate(lines, 1):
        stripped_line = line.strip()
        if not stripped_line or stripped_line.startswith('#'):
            continue

        parts = stripped_line.split()
        cmd = parts[0]
        args = parts[1:]

        try:
            if cmd == 'PUSH':
                n = int(args[0])
                stack.append(n)
            elif cmd == 'POP':
                if not stack:
                    raise IndexError(f"Stack underflow at line {line_num}")
                stack.pop()
            elif cmd == 'ADD':
                if len(stack) < 2:
                    raise IndexError(f"Not enough values on stack for ADD at line {line_num}")
                a, b = stack.pop(), stack.pop()
                stack.append(a + b)
            elif cmd == 'SUB':
                if len(stack) < 2:
                    raise IndexError(f"Not enough values on stack for SUB at line {line_num}")
                a, b = stack.pop(), stack.pop()
                stack.append(b - a)
            elif cmd == 'MUL':
                if len(stack) < 2:
                    raise IndexError(f"Not enough values on stack for MUL at line {line_num}")
                a, b = stack.pop(), stack.pop()
                stack.append(a * b)
            elif cmd == 'DIV':
                if len(stack) < 2:
                    raise IndexError(f"Not enough values on stack for DIV at line {line_num}")
                a, b = stack.pop(), stack.pop()
                if a == 0:
                    raise ZeroDivisionError(f"Division by zero at line {line_num}")
                stack.append(b // a)
            elif cmd == 'DUP':
                if not stack:
                    raise IndexError(f"Not enough values on stack for DUP at line {line_num}")
                stack.append(stack[-1])
            elif cmd == 'SWAP':
                if len(stack) < 2:
                    raise IndexError(f"Not enough values on stack for SWAP at line {line_num}")
                a, b = stack.pop(), stack.pop()
                stack.append(a)
                stack.append(b)
            elif cmd == 'PRINT':
                if not stack:
                    raise IndexError(f"No value to print at line {line_num}")
                output.append(str(stack[-1]))
        except (IndexError, ZeroDivisionError) as e:
            raise type(e)(f"{e.args[0]}") from None
    return output
