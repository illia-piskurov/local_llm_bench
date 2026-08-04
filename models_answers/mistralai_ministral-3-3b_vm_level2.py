def run(program: str) -> list[str]:
    stack = []
    output = []
    lines = program.split('\n')
    labels = {}
    pc = 0  # Программный счётчик
    line_num = 1

    def get_line():
        nonlocal pc, line_num
        while True:
            if pc >= len(lines):
                return None
            line = lines[pc].strip()
            pc += 1
            if not line or line.startswith('#'):
                continue
            return line.split()

    while True:
        try:
            cmd = get_line()
            if cmd is None:
                break

            stripped_line = ' '.join(cmd)
            parts = stripped_line.split(maxsplit=1)

            if parts[0] == 'LABEL':
                labels[parts[1]] = pc - 1
                continue

            try:
                if cmd[0] == 'PUSH':
                    n = int(cmd[1])
                    stack.append(n)
                elif cmd[0] == 'POP':
                    if not stack:
                        raise IndexError(f"Stack underflow at line {line_num}")
                    stack.pop()
                elif cmd[0] == 'ADD':
                    if len(stack) < 2:
                        raise IndexError(f"Not enough values on stack for ADD at line {line_num}")
                    a, b = stack.pop(), stack.pop()
                    stack.append(a + b)
                elif cmd[0] == 'SUB':
                    if len(stack) < 2:
                        raise IndexError(f"Not enough values on stack for SUB at line {line_num}")
                    a, b = stack.pop(), stack.pop()
                    stack.append(b - a)
                elif cmd[0] == 'MUL':
                    if len(stack) < 2:
                        raise IndexError(f"Not enough values on stack for MUL at line {line_num}")
                    a, b = stack.pop(), stack.pop()
                    stack.append(a * b)
                elif cmd[0] == 'DIV':
                    if len(stack) < 2:
                        raise IndexError(f"Not enough values on stack for DIV at line {line_num}")
                    a, b = stack.pop(), stack.pop()
                    if a == 0:
                        raise ZeroDivisionError(f"Division by zero at line {line_num}")
                    stack.append(b // a)
                elif cmd[0] == 'DUP':
                    if not stack:
                        raise IndexError(f"Not enough values on stack for DUP at line {line_num}")
                    stack.append(stack[-1])
                elif cmd[0] == 'SWAP':
                    if len(stack) < 2:
                        raise IndexError(f"Not enough values on stack for SWAP at line {line_num}")
                    a, b = stack.pop(), stack.pop()
                    stack.append(a)
                    stack.append(b)
                elif cmd[0] == 'PRINT':
                    if not stack:
                        raise IndexError(f"No value to print at line {line_num}")
                    output.append(str(stack[-1]))
            except (IndexError, ZeroDivisionError) as e:
                raise type(e)(f"{e.args[0]}") from None

            # Обработка условных переходов
            if cmd and len(cmd) > 1 and cmd[0] in ('JMP', 'JZ', 'JNZ'):
                label = cmd[1]
                if cmd[0] == 'JMP':
                    pc = labels.get(label, -1)
                    line_num = pc + 1
                    continue
                else:
                    val = stack.pop()
                    if (cmd[0] == 'JZ' and val == 0) or (cmd[0] == 'JNZ' and val != 0):
                        pc = labels.get(label, -1)
                        line_num = pc + 1
                        continue

            # Обработка ошибок некорректной метки
            if cmd and len(cmd) > 1:
                label = cmd[1]
                if label not in labels:
                    raise ValueError(f"Undefined label '{label}' at line {line_num}")

        except Exception as e:
            raise type(e)(f"{e.args[0]}") from None

    return output
