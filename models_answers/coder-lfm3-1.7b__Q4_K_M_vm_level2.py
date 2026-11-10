def run(program: str) -> list[str]:
    stack = []
    outputs = []
    labels = {}   # name -> line_number (1-indexed)

    lines = program.splitlines()
    i = 0
    n = len(lines)

    while i < n:
        raw_line = lines[i].strip()

        # skip empty or comment lines
        if not raw_line or raw_line.lstrip().startswith('#'):
            i += 1
            continue

        parts = raw_line.split()
        op = parts[0].upper() if parts else ''
        line_no = i + 1   # line numbers are 1‑based for error messages

        # ---- LABEL ----------------------------------------------------
        if op == 'LABEL':
            if len(parts) < 2:
                raise ValueError(f"line {line_no}: missing argument for LABEL")
            label_name = parts[1].strip().upper()
            labels[label_name] = line_no
            i += 1          # definition is not executed; move to next instruction
        # ---- JMP ------------------------------------------------------
        elif op == 'JMP':
            if len(parts) < 2:
                raise ValueError(f"line {line_no}: missing argument for JMP")
            target_label = parts[1].strip().upper()
            if target_label in labels:
                i = labels[target_label]   # jump over the current line and continue at label's definition line
                continue
            else:
                raise ValueError(f"line {line_no}: unknown jump target '{target_label}'")
        # ---- JZ ---------------------------------------------------------
        elif op == 'JZ':
            if not stack:
                raise ValueError(f"line {line_no}: JZ needs at least one item on the stack (pop value)")
            val = stack.pop()
            if val == 0:
                if len(parts) >= 2:
                    target_label = parts[1].strip().upper()
                    if target_label in labels:
                        i = labels[target_label]
                        continue
                    else:
                        raise ValueError(f"line {line_no}: JZ has no matching label")
                # if there is no target, fall through (no jump)
            else:
                i += 1   # normal execution: move to next line
        # ---- JNZ --------------------------------------------------------
        elif op == 'JNZ':
            if not stack:
                raise ValueError(f"line {line_no}: JNZ needs at least one item on the stack (pop value)")
            val = stack.pop()
            if val != 0:
                if len(parts) >= 2:
                    target_label = parts[1].strip().upper()
                    if target_label in labels:
                        i = labels[target_label]
                        continue
                    else:
                        raise ValueError(f"line {line_no}: JNZ has no matching label")
                # if no target, fall through
            else:
                i += 1   # normal execution
        # ---- PUSH -------------------------------------------------------
        elif op == 'PUSH':
            if len(parts) >= 2:
                try:
                    n = int(parts[1])
                except ValueError:
                    raise ValueError(f"line {line_no}: invalid number '{parts[1]}' for PUSH")
                stack.append(n)
            else:
                raise ValueError(f"line {line_no}: missing argument for PUSH (need a number)")
        # ---- POP ---------------------------------------------------------
        elif op == 'POP':
            if not stack:
                raise RuntimeError(f"line {line_no}: POP requires at least one item on the stack")
            stack.pop()
        # ---- ADD ---------------------------------------------------------
        elif op == 'ADD':
            if len(stack) < 2:
                raise ValueError(f"line {line_no}: ADD needs two operands, got {len(stack)} items")
            b = stack.pop()
            a = stack.pop()
            stack.append(a + b)
        # ---- SUB ---------------------------------------------------------
        elif op == 'SUB':
            if len(stack) < 2:
                raise ValueError(f"line {line_no}: SUB needs two operands, got {len(stack)} items")
            b = stack.pop()
            a = stack.pop()
            stack.append(a - b)
        # ---- MUL ---------------------------------------------------------
        elif op == 'MUL':
            if len(stack) < 2:
                raise ValueError(f"line {line_no}: MUL needs two operands, got {len(stack)} items")
            a = stack.pop()
            b = stack.pop()
            stack.append(a * b)
        # ---- DIV ---------------------------------------------------------
        elif op == 'DIV':
            if len(stack) < 2:
                raise ValueError(f"line {line_no}: DIV needs two operands, got {len(stack)} items")
            b = stack.pop()
            a = stack.pop()
            if b == 0:
                raise ZeroDivisionError(f"line {line_no}: DIV by zero (divisor = {b})")
            stack.append(a // b)
        # ---- DUP ---------------------------------------------------------
        elif op == 'DUP':
            if not stack:
                raise ValueError(f"line {line_no}: DUP requires at least one item to duplicate")
            stack.append(stack[-1])
        # ---- SWAP -------------------------------------------------------
        elif op == 'SWAP':
            if len(stack) < 2:
                raise ValueError(f"line {line_no}: SWAP needs two items, got only {len(stack)} on stack")
            b = stack.pop()
            a = stack.pop()
            stack.append(a)
            stack.append(b)
        # ---- PRINT ------------------------------------------------------
        elif op == 'PRINT':
            if not stack:
                raise ValueError(f"line {line_no}: PRINT on empty stack")
            outputs.append(str(stack[-1]))
        # ---- UNKNOWN ----------------------------------------------------
        else:
            raise ValueError(f"line {line_no}: unknown instruction '{op}'")

        i += 1   # advance to next line
    return outputs
