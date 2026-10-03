def run(program: str) -> list[str]:
    stack = []
    output = []
    lines = [line.strip() for line in program.split('\n') if line.strip() and not line.startswith('#')]
    labels = {}
    pc = 0  # Program counter

    def get_label(name):
        return next((i for i, l in enumerate(lines) if l.startswith(f"{name}:")), None)

    while pc < len(lines):
        line = lines[pc].split()
        cmd = line[0] if line else ''

        try:
            if not cmd:
                pc += 1
                continue

            if cmd == 'PUSH':
                n = int(line[1])
                stack.append(n)
            elif cmd == 'POP':
                if len(stack) == 0:
                    raise ValueError(f"Stack underflow at line {pc + 1}")
                stack.pop()
            elif cmd == 'ADD':
                if len(stack) < 2:
                    raise ValueError(f"Not enough values for ADD at line {pc + 1}")
                a, b = stack.pop(), stack.pop()
                stack.append(a + b)
            elif cmd == 'SUB':
                if len(stack) < 2:
                    raise ValueError(f"Not enough values for SUB at line {pc + 1}")
                a, b = stack.pop(), stack.pop()
                stack.append(b - a)
            elif cmd == 'MUL':
                if len(stack) < 2:
                    raise ValueError(f"Not enough values for MUL at line {pc + 1}")
                a, b = stack.pop(), stack.pop()
                stack.append(a * b)
            elif cmd == 'DIV':
                if len(stack) < 2:
                    raise ValueError(f"Not enough values for DIV at line {pc + 1}")
                a, b = stack.pop(), stack.pop()
                if b == 0:
                    raise ZeroDivisionError(f"Division by zero at line {pc + 1}")
                stack.append(a // b)
            elif cmd == 'DUP':
                if len(stack) == 0:
                    raise ValueError(f"Not enough values for DUP at line {pc + 1}")
                stack.append(stack[-1])
            elif cmd == 'SWAP':
                if len(stack) < 2:
                    raise ValueError(f"Not enough values for SWAP at line {pc + 1}")
                a, b = stack.pop(), stack.pop()
                stack.append(a)
                stack.append(b)
            elif cmd == 'PRINT':
                if len(stack) == 0:
                    raise ValueError(f"No value to print at line {pc + 1}")
                output.append(str(stack[-1]))
            elif cmd == 'LABEL':
                pass
            elif cmd == 'JMP':
                label_name = line[1]
                target_pos = get_label(label_name)
                if target_pos is None:
                    raise ValueError(f"Undefined label '{label_name}' at line {pc + 1}")
                pc = target_pos - 1
            elif cmd == 'JZ':
                if len(stack) == 0:
                    raise ValueError(f"Not enough values for JZ at line {pc + 1}")
                value = stack.pop()
                label_name = line[1]
                target_pos = get_label(label_name)
                if target_pos is None:
                    raise ValueError(f"Undefined label '{label_name}' at line {pc + 1}")
                pc = target_pos - 1 if value == 0 else pc
            elif cmd == 'JNZ':
                if len(stack) == 0:
                    raise ValueError(f"Not enough values for JNZ at line {pc + 1}")
                value = stack.pop()
                label_name = line[1]
                target_pos = get_label(label_name)
                if target_pos is None:
                    raise ValueError(f"Undefined label '{label_name}' at line {pc + 1}")
                pc = target_pos - 1 if value != 0 else pc
            else:
                raise ValueError(f"Unknown command '{cmd}' at line {pc + 1}")

        except (ValueError, ZeroDivisionError) as e:
            raise e

        pc += 1
    return output
