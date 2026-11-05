def run(program: str) -> list[str]:
    lines = program.splitlines()
    # collect non-comment, non-empty lines with original line numbers (1-indexed)
    parsed = []          # each element: (cmd, args_tuple, orig_line)
    labels = {}         # name -> orig_line (the line number where label appears)

    for orig_idx, raw in enumerate(lines, 1):
        line = raw.strip()
        if not line or line.startswith('#'):
            continue
        parts = line.split()
        cmd = parts[0]

        if cmd == 'LABEL':
            if len(parts) < 2:
                raise RuntimeError(f"Line {orig_idx}: LABEL needs a name") from None
            name = parts[1]
            labels[name] = orig_idx
            parsed.append(('LABEL', (), orig_idx))
        else:
            if cmd in ('JMP', 'JZ', 'JNZ'):
                if len(parts) < 2:
                    raise RuntimeError(f"Line {orig_idx}: {cmd} needs a label") from None
                label_name = parts[1]
                if label_name not in labels:
                    raise RuntimeError(f"Line {orig_idx}: {cmd} references undefined label '{label_name}'") from None
                args = (label_name,)
            elif cmd in ('PUSH', 'POP', 'ADD', 'SUB', 'MUL', 'DIV', 'DUP', 'SWAP', 'PRINT'):
                if cmd == 'PUSH':
                    if len(parts) < 2:
                        raise RuntimeError(f"Line {orig_idx}: PUSH needs an integer") from None
                    try:
                        n = int(parts[1])
                    except ValueError:
                        raise RuntimeError(f"Line {orig_idx}: PUSH argument not an integer") from None
                    args = (n,)
                elif cmd == 'POP' or cmd in ('DUP', 'SWAP', 'PRINT'):
                    args = ()
                else:  # ADD, SUB, MUL, DIV
                    args = ()
            else:
                raise RuntimeError(f"Line {orig_idx}: Unknown instruction '{cmd}'") from None

            parsed.append((cmd, args, orig_idx))

    # map label name to the smallest orig_line where it appears (already single definition)
    # for execution we need to find the instruction index corresponding to a label's orig_line
    # build dict label_to_exec_idx
    label_to_exec_idx = {}
    for idx, (cmd, args, orig_line) in enumerate(parsed):
        if cmd == 'LABEL':
            name = args[0] if args else ''
            label_to_exec_idx[name] = idx   # label instruction itself

    # execute
    stack = []
    output = []
    i = 0
    while i < len(parsed):
        cmd, args, orig_line = parsed[i]

        if cmd == 'LABEL':
            # do nothing
            i += 1
            continue

        if cmd == 'PUSH':
            n = args[0]
            stack.append(n)
            i += 1
            continue

        if cmd == 'POP':
            if not stack:
                raise RuntimeError(f"Line {orig_line}: POP on empty stack") from None
            stack.pop()
            i += 1
            continue

        if cmd == 'ADD':
            if len(stack) < 2:
                raise RuntimeError(f"Line {orig_line}: ADD needs two values") from None
            b = stack.pop()
            a = stack.pop()
            stack.append(a + b)
            i += 1
            continue

        if cmd == 'SUB':
            if len(stack) < 2:
                raise RuntimeError(f"Line {orig_line}: SUB needs two values") from None
            b = stack.pop()
            a = stack.pop()
            stack.append(a - b)
            i += 1
            continue

        if cmd == 'MUL':
            if len(stack) < 2:
                raise RuntimeError(f"Line {orig_line}: MUL needs two values") from None
            b = stack.pop()
            a = stack.pop()
            stack.append(a * b)
            i += 1
            continue

        if cmd == 'DIV':
            if len(stack) < 2:
                raise RuntimeError(f"Line {orig_line}: DIV needs two values") from None
            b = stack.pop()
            a = stack.pop()
            if b == 0:
                raise RuntimeError(f"Line {orig_line}: Division by zero") from None
            stack.append(a // b)
            i += 1
            continue

        if cmd == 'DUP':
            if not stack:
                raise RuntimeError(f"Line {orig_line}: DUP on empty stack") from None
            stack.append(stack[-1])
            i += 1
            continue

        if cmd == 'SWAP':
            if len(stack) < 2:
                raise RuntimeError(f"Line {orig_line}: SWAP needs at least two values") from None
            a = stack[-2]
            b = stack[-1]
            stack[-2] = b
            stack[-1] = a
            i += 1
            continue

        if cmd == 'PRINT':
            if not stack:
                raise RuntimeError(f"Line {orig_line}: PRINT on empty stack") from None
            val = stack[-1]
            output.append(str(val))
            i += 1
            continue

        if cmd == 'JMP':
            label_name = args[0]
            if label_name not in label_to_exec_idx:
                raise RuntimeError(f"Line {orig_line}: JMP references undefined label '{label_name}'") from None
            target_idx = label_to_exec_idx[label_name]
            i = target_idx
            continue

        if cmd == 'JZ':
            label_name = args[0]
            if label_name not in label_to_exec_idx:
                raise RuntimeError(f"Line {orig_line}: JZ references undefined label '{label_name}'") from None
            if not stack:
                raise RuntimeError(f"Line {orig_line}: JZ needs a value on stack") from None
            val = stack.pop()
            if val == 0:
                target_idx = label_to_exec_idx[label_name]
                i = target_idx
            else:
                i += 1
            continue

        if cmd == 'JNZ':
            label_name = args[0]
            if label_name not in label_to_exec_idx:
                raise RuntimeError(f"Line {orig_line}: JNZ references undefined label '{label_name}'") from None
            if not stack:
                raise RuntimeError(f"Line {orig_line}: JNZ needs a value on stack") from None
            val = stack.pop()
            if val != 0:
                target_idx = label_to_exec_idx[label_name]
                i = target_idx
            else:
                i += 1
            continue

        # should not reach here
        i += 1

    return output
