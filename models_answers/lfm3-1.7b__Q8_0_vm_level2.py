def run(program: str) -> list[str]:
    output = []
    stack = []
    lines = program.splitlines()
    i = 1  # line numbers are 1-indexed
    labels = {}  # name -> line number (where the label is defined)

    while i <= len(lines):
        raw_line = lines[i - 1]
        stripped = raw_line.strip()

        if not stripped or stripped.startswith('#'):
            i += 1
            continue

        parts = raw_line.split()
        cmd = parts[0].upper()

        # PUSH <n>
        if cmd == 'PUSH':
            if len(parts) < 2:
                raise ValueError(f"Line {i}: PUSH requires an argument (e.g., PUSH <n>)")
            try:
                n = int(parts[1])
            except ValueError:
                raise ValueError(f"Line {i}: PUSH expects integer, got '{parts[1]}'")
            stack.append(n)

        # POP
        elif cmd == 'POP':
            if len(stack) == 0:
                raise IndexError(f"Line {i}: POP from empty stack")
            stack.pop()

        # ADD
        elif cmd == 'ADD':
            if len(stack) < 2:
                raise ValueError(f"Line {i}: ADD needs two operands, got {len(stack)} on stack")
            b = stack.pop()   # topmost
            a = stack.pop()   # next
            stack.append(a + b)

        # SUB
        elif cmd == 'SUB':
            if len(stack) < 2:
                raise ValueError(f"Line {i}: SUB needs two operands, got {len(stack)} on stack")
            b = stack.pop()
            a = stack.pop()
            stack.append(a - b)

        # MUL
        elif cmd == 'MUL':
            if len(stack) < 2:
                raise ValueError(f"Line {i}: MUL needs two operands, got {len(stack)} on stack")
            b = stack.pop()
            a = stack.pop()
            stack.append(a * b)

        # DIV
        elif cmd == 'DIV':
            if len(stack) < 2:
                raise ValueError(f"Line {i}: DIV needs two operands, got {len(stack)} on stack")
            b = stack.pop()
            a = stack.pop()
            if b == 0:
                raise ZeroDivisionError(f"Line {i}: Division by zero (b = {b})")
            stack.append(a // b)

        # DUP
        elif cmd == 'DUP':
            if len(stack) == 0:
                raise IndexError(f"Line {i}: DUP on empty stack")
            top = stack.pop()
            stack.append(top)

        # SWAP
        elif cmd == 'SWAP':
            if len(stack) < 2:
                raise ValueError(f"Line {i}: SWAP needs two values, got {len(stack)} on stack")
            b = stack.pop()   # top
            a = stack.pop()   # next
            stack.append(b)
            stack.append(a)

        # PRINT
        elif cmd == 'PRINT':
            if len(stack) == 0:
                raise IndexError(f"Line {i}: PRINT from empty stack")
            value = stack[-1]
            output.append(str(value))

        # LABEL <name>
        elif cmd == 'LABEL':
            if len(parts) < 2:
                raise ValueError(f"Line {i}: LABEL requires an argument (e.g., LABEL <name>)")
            name = parts[1]
            labels[name] = i

        # JMP <name>
        elif cmd == 'JMP':
            if len(parts) < 2:
                raise ValueError(f"Line {i}: JMP requires an argument (e.g., JMP <name>)")
            name = parts[1]
            target_line = labels.get(name)
            if target_line is None:
                raise ValueError(f"Line {i}: Label '{name}' not defined")
            i = target_line

        # JZ <name>
        elif cmd == 'JZ':
            if len(parts) < 2:
                raise ValueError(f"Line {i}: JZ requires an argument (e.g., JZ <name>)")
            name = parts[1]
            if len(stack) == 0:
                raise IndexError(f"Line {i}: JZ needs a value on stack")
            val = stack.pop()
            if val == 0:
                # jump to label
                target_line = labels.get(name)
                if target_line is not None:
                    i = target_line

        # JNZ <name>
        elif cmd == 'JNZ':
            if len(parts) < 2:
                raise ValueError(f"Line {i}: JNZ requires an argument (e.g., JNZ <name>)")
            name = parts[1]
            if len(stack) == 0:
                raise IndexError(f"Line {i}: JNZ needs a value on stack")
            val = stack.pop()
            if val != 0:
                target_line = labels.get(name)
                if target_line is not None:
                    i = target_line

        # Default unknown command
        else:
            raise ValueError(f"Unknown command '{cmd}' at line {i}")

        i += 1  # move to next line after processing a normal instruction

    return output
