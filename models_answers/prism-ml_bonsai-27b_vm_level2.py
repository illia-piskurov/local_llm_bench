def run(program: str) -> list[str]:
    stack = []
    output_lines = []
    lines = program.splitlines()
    n_lines = len(lines)

    # Предварительный проход для поиска меток
    label_map = {}
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            continue
        parts = stripped.split()
        if parts and parts[0] == 'LABEL':
            if len(parts) < 2:
                raise ValueError(f"Line {i+1}: LABEL requires a name")
            label_map[parts[1]] = i

    pc = 0
    while pc < n_lines:
        line = lines[pc]
        stripped = line.strip()
        
        # Игнорируем пустые строки и комментарии, но сохраняем номер строки для ошибок
        if not stripped or stripped.startswith('#'):
            pc += 1
            continue

        parts = stripped.split()
        command = parts[0]

        try:
            if command == 'PUSH':
                if len(parts) < 2:
                    raise ValueError(f"Line {pc+1}: PUSH requires an argument")
                stack.append(int(parts[1]))

            elif command == 'POP':
                if len(stack) < 1:
                    raise RuntimeError(f"Line {pc+1}: Stack underflow (empty stack)")
                stack.pop()

            elif command == 'ADD':
                if len(stack) < 2:
                    raise RuntimeError(f"Line {pc+1}: Stack underflow (need 2 values for ADD)")
                b = stack.pop(); a = stack.pop()
                stack.append(a + b)

            elif command == 'SUB':
                if len(stack) < 2:
                    raise RuntimeError(f"Line {pc+1}: Stack underflow (need 2 values for SUB)")
                b = stack.pop(); a = stack.pop()
                stack.append(a - b)

            elif command == 'MUL':
                if len(stack) < 2:
                    raise RuntimeError(f"Line {pc+1}: Stack underflow (need 2 values for MUL)")
                b = stack.pop(); a = stack.pop()
                stack.append(a * b)

            elif command == 'DIV':
                if len(stack) < 2:
                    raise RuntimeError(f"Line {pc+1}: Stack underflow (need 2 values for DIV)")
                b = stack.pop(); a = stack.pop()
                if b == 0:
                    raise ZeroDivisionError(f"Line {pc+1}: Division by zero")
                stack.append(a // b)

            elif command == 'DUP':
                if len(stack) < 1:
                    raise RuntimeError(f"Line {pc+1}: Stack underflow (need 1 value for DUP)")
                top = stack[-1]
                stack.append(top)

            elif command == 'SWAP':
                if len(stack) < 2:
                    raise RuntimeError(f"Line {pc+1}: Stack underflow (need 2 values for SWAP)")
                b = stack.pop(); a = stack.pop()
                stack.append(b); stack.append(a)

            elif command == 'PRINT':
                if len(stack) < 1:
                    raise RuntimeError(f"Line {pc+1}: Stack underflow (need 1 value for PRINT)")
                output_lines.append(str(stack[-1]))

            elif command == 'LABEL':
                # Метка просто помечает текущую позицию, при выполнении ничего не делает
                pass

            elif command == 'JMP':
                if len(parts) < 2:
                    raise ValueError(f"Line {pc+1}: JMP requires a label")
                target = parts[1]
                if target not in label_map:
                    raise NameError(f"Line {pc+1}: Undefined label '{target}'")
                pc = label_map[target]

            elif command == 'JZ':
                if len(parts) < 2:
                    raise ValueError(f"Line {pc+1}: JZ requires a label")
                target = parts[1]
                if target not in label_map:
                    raise NameError(f"Line {pc+1}: Undefined label '{target}'")

                if len(stack) < 1:
                    raise RuntimeError(f"Line {pc+1}: Stack underflow (need 1 value for JZ)")
                val = stack.pop()
                if val == 0:
                    pc = label_map[target]

            elif command == 'JNZ':
                if len(parts) < 2:
                    raise ValueError(f"Line {pc+1}: JNZ requires a label")
                target = parts[1]
                if target not in label_map:
                    raise NameError(f"Line {pc+1}: Undefined label '{target}'")

                if len(stack) < 1:
                    raise RuntimeError(f"Line {pc+1}: Stack underflow (need 1 value for JNZ)")
                val = stack.pop()
                if val != 0:
                    pc = label_map[target]

            else:
                raise ValueError(f"Line {pc+1}: Unknown command '{command}'")

        except Exception as e:
            # Перехватываем и перекидаем ошибку, сохраняя контекст строки в сообщении
            raise e

    return output_lines
