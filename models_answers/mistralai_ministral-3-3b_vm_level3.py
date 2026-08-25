def run(program: str) -> list[str]:
    stack = []
    output = []
    variables = {}
    call_stack = []  # Для хранения адресов возврата при CALL
    lines = program.split('\n')
    labels = {}
    pc = 0  # Program Counter
    line_map = {i+1: line for i, line in enumerate(lines)}

    while True:
        line_num = pc + 1
        if pc >= len(lines) or not lines[pc].strip():
            break

        stripped_line = lines[pc].strip()
        if not stripped_line or stripped_line.startswith('#'):
            pc += 1
            continue

        parts = stripped_line.split()
        cmd = parts[0]
        args = parts[1:]

        try:
            if cmd == 'LABEL':
                labels[args[0]] = line_num - 1
                pc += 1
            elif cmd in ('JMP', 'JZ', 'JNZ'):
                target_label = args[0]
                if target_label not in labels:
                    raise IndexError(f"Undefined label '{target_label}' at line {line_num}")
                target_pos = labels[target_label] - pc
                if cmd == 'JMP':
                    pc += target_pos
                elif cmd == 'JZ':
                    if stack and stack.pop() == 0:
                        pc += target_pos
                    else:
                        pc += 1
                elif cmd == 'JNZ':
                    if stack and stack.pop() != 0:
                        pc += target_pos
                    else:
                        pc += 1
            elif cmd == 'CALL':
                target_label = args[0]
                if target_label not in labels:
                    raise IndexError(f"Undefined label '{target_label}' at line {line_num}")
                call_stack.append(pc + 1)  # Сохраняем текущий PC как адрес возврата
                pc = labels[target_label] - pc
            elif cmd == 'RET':
                if not call_stack:
                    raise IndexError("Stack of calls is empty at RET")
                pc = call_stack.pop() - 1  # Переход к следующему инструкции после CALL
            elif cmd in ('EQ', 'GT', 'LT'):
                if len(stack) < 2:
                    raise IndexError(f"Not enough values on stack for comparison at line {line_num}")
                b, a = stack.pop(), stack.pop()
                result = 1 if (cmd == 'EQ' and a == b) else (
                    1 if cmd == 'GT' and a > b else
                    1 if cmd == 'LT' and a < b else 0)
                stack.append(result)
            elif cmd == 'STORE':
                var_name = args[0]
                if not stack:
                    raise IndexError(f"No value to store in variable '{var_name}' at line {line_num}")
                variables[var_name] = stack.pop()
            elif cmd == 'LOAD':
                var_name = args[0]
                if var_name not in variables:
                    raise IndexError(f"Variable '{var_name}' is not defined at line {line_num}")
                stack.append(variables[var_name])
            else:  # Original commands
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
                pc += 1
        except Exception as e:
            raise type(e)(f"Error at line {line_num}: {str(e)}")
    return output
