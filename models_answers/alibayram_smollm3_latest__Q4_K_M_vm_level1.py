def run(program: str) -> list[str]:
    stack = []
    line_num = 0
    output = []
    for line in program.strip().split('\n'):
        line_num += 1
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        if line.startswith('PUSH'):
            try:
                stack.append(int(line.split()[1]))
            except ValueError:
                raise ValueError(f"Invalid number on line {line_num}")
        elif line == 'POP':
            if len(stack) < 1:
                raise ValueError(f"Not enough values on line {line_num}")
            output.append(str(stack.pop()))
        elif line == 'ADD':
            if len(stack) < 2:
                raise ValueError(f"Not enough values on line {line_num}")
            a = stack.pop()
            b = stack.pop()
            stack.append(a + b)
            output.append(str(a + b))
        elif line == 'SUB':
            if len(stack) < 2:
                raise ValueError(f"Not enough values on line {line_num}")
            a = stack.pop()
            b = stack.pop()
            if b == 0:
                raise ValueError(f"Division by zero on line {line_num}")
            stack.append(a - b)
            output.append(str(a - b))
        elif line == 'MUL':
            if len(stack) < 2:
                raise ValueError(f"Not enough values on line {line_num}")
            a = stack.pop()
            b = stack.pop()
            if b == 0:
                raise ValueError(f"Division by zero on line {line_num}")
            stack.append(a * b)
            output.append(str(a * b))
        elif line == 'DIV':
            if len(stack) < 2:
                raise ValueError(f"Not enough values on line {line_num}")
            a = stack.pop()
            b = stack.pop()
            if b == 0:
                raise ValueError(f"Division by zero on line {line_num}")
            stack.append(a // b)
            output.append(str(a // b))
        elif line == 'DUP':
            if len(stack) < 1:
                raise ValueError(f"Not enough values on line {line_num}")
            stack.append(stack[-1])
        elif line == 'SWAP':
            if len(stack) < 2:
                raise ValueError(f"Not enough values on line {line_num}")
            a = stack.pop()
            b = stack.pop()
            stack.append(a)
            stack.append(b)
        elif line == 'PRINT':
            if len(stack) < 1:
                raise ValueError(f"Not enough values on line {line_num}")
            output.append(str(stack[-1]))
        else:
            raise ValueError(f"Unknown instruction on line {line_num}")
    return output
