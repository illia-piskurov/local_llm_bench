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
        cmd = line[0]

        try:
            if cmd == 'PUSH':
                n = int(line[1])
                stack.append(n)
            elif cmd == 'POP':
                if not stack:
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
                if not stack:
                    raise ValueError(f"Not enough values for DUP at line {pc + 1}")
                stack.append(stack[-1])
            elif cmd == 'SWAP':
                if len(stack) < 2:
                    raise ValueError(f"Not enough values for SWAP at line {pc + 1}")
                a, b = stack.pop(), stack.pop()
                stack.append(a)
                stack.append(b)
            elif cmd == 'PRINT':
                if not stack:
                    raise ValueError(f"No value to print at line {pc + 1}")
                output.append(str(stack[-1]))
            elif cmd == 'LABEL':
                pass
            elif cmd == 'JMP':
                target = get_label(line[1])
                if target is None:
                    raise ValueError(f"Undefined label '{line[1]}' at line {pc + 1}")
                pc = target - 1
            elif cmd == 'JZ':
                if not stack:
                    raise ValueError(f"Not enough values for JZ at line {pc + 1}")
                val = stack.pop()
                target = get_label(line[1])
                if target is None:
                    raise ValueError(f"Undefined label '{line[1]}' at line {pc + 1}")
                pc = (target - 1) if val == 0 else pc
            elif cmd == 'JNZ':
                if not stack:
                    raise ValueError(f"Not enough values for JNZ at line {pc + 1}")
                val = stack.pop()
                target = get_label(line[1])
                if target is None:
                    raise ValueError(f"Undefined label '{line[1]}' at line {pc + 1}")
                pc = (target - 1) if val != 0 else pc
            else:
                raise ValueError(f"Unknown command '{cmd}' at line {pc + 1}")
        except Exception as e:
            raise ValueError(str(e))
        pc += 1

    return output
