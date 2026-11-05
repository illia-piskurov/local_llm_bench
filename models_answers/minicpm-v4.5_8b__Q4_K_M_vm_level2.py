def run(program: str) -> list[str]:
    lines = [line.strip() for line in program.splitlines() if line.strip()]
    labels = {}
    pc = 0
    stack = []
    output = []
    while pc < len(lines):
        line = lines[pc]
        if line.startswith('#') or not line:
            pc += 1
            continue
        parts = line.split()
        if not parts:
            pc += 1
            continue
        cmd = parts[0]
        if cmd == 'LABEL':
            name = parts[1]
            labels[name] = pc
        elif cmd == 'JMP':
            name = parts[1]
            if name not in labels:
                raise ValueError(f"Line {pc+1}: JMP: unknown label {name}")
            pc = labels[name]
        elif cmd == 'JZ':
            name = parts[1]
            if name not in labels:
                raise ValueError(f"Line {pc+1}: JZ: unknown label {name}")
            if not stack:
                raise ValueError(f"Line {pc+1}: JZ: stack is empty")
            val = stack.pop()
            if val == 0:
                pc = labels[name]
        elif cmd == 'JNZ':
            name = parts[1]
            if name not in labels:
                raise ValueError(f"Line {pc+1}: JNZ: unknown label {name}")
            if not stack:
                raise ValueError(f"Line {pc+1}: JNZ: stack is empty")
            val = stack.pop()
            if val != 0:
                pc = labels[name]
        else:
            if cmd == 'PUSH':
                try:
                    n = int(parts[1])
                    stack.append(n)
                except (IndexError, ValueError):
                    raise ValueError(f"Line {pc+1}: PUSH: missing argument")
            elif cmd == 'POP':
                if not stack:
                    raise ValueError(f"Line {pc+1}: POP: stack is empty")
                stack.pop()
            elif cmd == 'ADD':
                if len(stack) < 2:
                    raise ValueError(f"Line {pc+1}: ADD: stack has less than 2 values")
                b = stack.pop()
                a = stack.pop()
                stack.append(a + b)
            elif cmd == 'SUB':
                if len(stack) < 2:
                    raise ValueError(f"Line {pc+1}: SUB: stack has less than 2 values")
                b = stack.pop()
                a = stack.pop()
                stack.append(a - b)
            elif cmd == 'MUL':
                if len(stack) < 2:
                    raise ValueError(f"Line {pc+1}: MUL: stack has less than 2 values")
                b = stack.pop()
                a = stack.pop()
                stack.append(a * b)
            elif cmd == 'DIV':
                if len(stack) < 2:
                    raise ValueError(f"Line {pc+1}: DIV: stack has less than 2 values")
                b = stack.pop()
                a = stack.pop()
                if b == 0:
                    raise ValueError(f"Line {pc+1}: DIV: division by zero")
                stack.append(a // b)
            elif cmd == 'DUP':
                if len(stack) < 1:
                    raise ValueError(f"Line {pc+1}: DUP: stack is empty")
                stack.append(stack[-1])
            elif cmd == 'SWAP':
                if len(stack) < 2:
                    raise ValueError(f"Line {pc+1}: SWAP: stack has less than 2 values")
                stack[-2], stack[-1] = stack[-1], stack[-2]
            elif cmd == 'PRINT':
                if not stack:
                    raise ValueError(f"Line {pc+1}: PRINT: stack is empty")
                output.append(str(stack[-1]))
            else:
                raise ValueError(f"Line {pc+1}: Unknown command: {cmd}")
        pc += 1
    return output
