def run(program: str) -> list[str]:
    lines = program.splitlines()
    parsed = []
    labels = {}
    vars_mem = {}
    call_stack = []

    for orig_idx, raw in enumerate(lines, 1):
        line = raw.strip()
        if not line or line.startswith('#'):
            continue
        parts = line.split()
        cmd = parts[0]

        if cmd == 'LABEL':
            if len(parts) < 2:
                raise RuntimeError(f"Line {orig_idx}: LABEL needs a name")
            name = parts[1]
            labels[name] = orig_idx
            parsed.append(('LABEL', (), orig_idx))
        else:
            if cmd in ('CALL', 'RET', 'STORE', 'LOAD', 'JMP', 'JZ', 'JNZ'):
                if len(parts) < 2:
                    raise RuntimeError(f"Line {orig_idx}: {cmd} needs a name/label")
                arg = parts[1]
                args = (arg,)
            elif cmd in ('PUSH', 'EQ', 'GT', 'LT'):
                if cmd == 'PUSH':
                    if len(parts) < 2:
                        raise RuntimeError(f"Line {orig_idx}: PUSH needs an integer")
                    try:
                        n = int(parts[1])
                    except ValueError:
                        raise RuntimeError(f"Line {orig_idx}: PUSH argument not an integer")
                    args = (n,)
                else:
                    args = ()
            elif cmd in ('POP', 'DUP', 'SWAP', 'PRINT'):
                args = ()
            else:
                raise RuntimeError(f"Line {orig_idx}: Unknown instruction '{cmd}'")
            parsed.append((cmd, args, orig_idx))

    label_to_exec_idx = {}
    for idx, (cmd, args, orig_line) in enumerate(parsed):
        if cmd == 'LABEL':
            name = args[0] if args else ''
            label_to_exec_idx[name] = idx

    i = 0
    stack = []
    output = []
    while i < len(parsed):
        cmd, args, orig_line = parsed[i]

        if cmd == 'LABEL':
            i += 1
            continue

        if cmd == 'PUSH':
            n = args[0]
            stack.append(n)
            i += 1
            continue

        if cmd == 'POP':
            if not stack:
                raise RuntimeError(f"Line {orig_line}: POP on empty stack")
            stack.pop()
            i += 1
            continue

        if cmd == 'ADD':
            if len(stack) < 2:
                raise RuntimeError(f"Line {orig_line}: ADD needs two values")
            b = stack.pop()
            a = stack.pop()
            stack.append(a + b)
            i += 1
            continue

        if cmd == 'SUB':
            if len(stack) < 2:
                raise RuntimeError(f"Line {orig_line}: SUB needs two values")
            b = stack.pop()
            a = stack.pop()
            stack.append(a - b)
            i += 1
            continue

        if cmd == 'MUL':
            if len(stack) < 2:
                raise RuntimeError(f"Line {orig_line}: MUL needs two values")
            b = stack.pop()
            a = stack.pop()
            stack.append(a * b)
            i += 1
            continue

        if cmd == 'DIV':
            if len(stack) < 2:
                raise RuntimeError(f"Line {orig_line}: DIV needs two values")
            b = stack.pop()
            a = stack.pop()
            if b == 0:
                raise RuntimeError(f"Line {orig_line}: Division by zero")
            stack.append(a // b)
            i += 1
            continue

        if cmd == 'DUP':
            if not stack:
                raise RuntimeError(f"Line {orig_line}: DUP on empty stack")
            stack.append(stack[-1])
            i += 1
            continue

        if cmd == 'SWAP':
            if len(stack) < 2:
                raise RuntimeError(f"Line {orig_line}: SWAP needs at least two values")
            a = stack[-2]
            b = stack[-1]
            stack[-2] = b
            stack[-1] = a
            i += 1
            continue

        if cmd == 'PRINT':
            if not stack:
                raise RuntimeError(f"Line {orig_line}: PRINT on empty stack")
            val = stack[-1]
            output.append(str(val))
            i += 1
            continue

        if cmd == 'CALL':
            name = args[0]
            if name not in label_to_exec_idx:
                raise RuntimeError(f"Line {orig_line}: CALL references undefined label '{name}'")
            call_stack.append(i)          # return to current instruction+1
            i = label_to_exec_idx[name]
            continue

        if cmd == 'RET':
            if not call_stack:
                raise RuntimeError(f"Line {orig_line}: RET with empty call stack")
            i = call_stack.pop()
            continue

        if cmd == 'STORE':
            var = args[0]
            if not stack:
                raise RuntimeError(f"Line {orig_line}: STORE needs a value")
            val = stack.pop()
            vars_mem[var] = val
            i += 1
            continue

        if cmd == 'LOAD':
            var = args[0]
            if var not in vars_mem:
                raise RuntimeError(f"Line {orig_line}: LOAD references undefined variable '{var}'")
            stack.append(vars_mem[var])
            i += 1
            continue

        if cmd == 'JMP':
            name = args[0]
            if name not in label_to_exec_idx:
                raise RuntimeError(f"Line {orig_line}: JMP references undefined label '{name}'")
            i = label_to_exec_idx[name]
            continue

        if cmd == 'JZ':
            name = args[0]
            if name not in label_to_exec_idx:
                raise RuntimeError(f"Line {orig_line}: JZ references undefined label '{name}'")
            if not stack:
                raise RuntimeError(f"Line {orig_line}: JZ needs a value")
            val = stack.pop()
            if val == 0:
                i = label_to_exec_idx[name]
            else:
                i += 1
            continue

        if cmd == 'JNZ':
            name = args[0]
            if name not in label_to_exec_idx:
                raise RuntimeError(f"Line {orig_line}: JNZ references undefined label '{name}'")
            if not stack:
                raise RuntimeError(f"Line {orig_line}: JNZ needs a value")
            val = stack.pop()
            if val != 0:
                i = label_to_exec_idx[name]
            else:
                i += 1
            continue

        if cmd in ('EQ', 'GT', 'LT'):
            if len(stack) < 2:
                raise RuntimeError(f"Line {orig_line}: {cmd} needs two values")
            b = stack.pop()
            a = stack.pop()
            if cmd == 'EQ':
                res = 1 if a == b else 0
            elif cmd == 'GT':
                res = 1 if a > b else 0
            elif cmd == 'LT':
                res = 1 if a < b else 0
            else:
                raise RuntimeError(f"Line {orig_line}: Unknown comparison '{cmd}'")
            stack.append(res)
            i += 1
            continue

        i += 1

    return output
