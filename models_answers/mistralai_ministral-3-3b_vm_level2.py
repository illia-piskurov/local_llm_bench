def run(program):
    stack = []
    output = []
    labels = {}
    lines = program.split('\n')
    current_line = 0

    # Парсим метки
    for line_num, line in enumerate(lines):
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            continue
        parts = stripped.split()
        if parts and parts[0] == 'LABEL':
            labels[parts[1]] = line_num

    # Выполнение программы с отслеживанием индексации
    pc = 0  # Программный указатель
    while True:
        line = lines[pc].strip()
        if not line or line.startswith('#'):
            pc += 1
            continue

        parts = line.split()
        cmd = parts[0]

        try:
            if cmd == 'PUSH':
                stack.append(int(parts[1]))
            elif cmd == 'POP':
                if not stack: raise IndexError(f"Stack underflow at line {pc + 1}")
                stack.pop()
            elif cmd in ('ADD', 'SUB', 'MUL'):
                if len(stack) < 2:
                    raise IndexError(f"Not enough values for {cmd} at line {pc + 1}")

                a, b = stack.pop(), stack.pop() if cmd == 'ADD' else stack[-1], stack.pop()
                if cmd == 'SUB': a, b = b, a
                stack.append(a + (b * (cmd != 'ADD')))

            elif cmd == 'DIV':
                if len(stack) < 2:
                    raise IndexError(f"Not enough values for DIV at line {pc + 1}")
                a, b = stack.pop(), stack.pop()
                if a == 0: raise ZeroDivisionError(f"Division by zero at line {pc + 1}")
                stack.append(b // a)

            elif cmd == 'DUP':
                if not stack:
                    raise IndexError(f"No values to duplicate at line {pc + 1}")
                stack.append(stack[-1])

            elif cmd == 'SWAP':
                if len(stack) < 2:
                    raise IndexError(f"Not enough values for SWAP at line {pc + 1}")
                a, b = stack.pop(), stack.pop()
                stack.extend([a, b])

            elif cmd == 'PRINT':
                if not stack:
                    raise IndexError(f"No value to print at line {pc + 1}")
                output.append(str(stack[-1]))

            elif cmd in ('JMP', 'JZ', 'JNZ'):
                target = parts[1]
                if cmd == 'JMP' or (cmd == 'JZ' and stack.pop() == 0) or (cmd == 'JNZ' and stack.pop() != 0):
                    if target not in labels:
                        raise IndexError(f"Undefined label '{target}' at line {pc + 1}")
                    pc = labels[target]

            else:  # LABEL
                pass

        except Exception as e:
            raise type(e)(f"{e}") from None

        pc += 1

    return output
