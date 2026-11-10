def run(program: str) -> list[str]:
    output = []
    stack = []                     # holds integer values for arithmetic operations
    call_stack = []                # returns addresses (line numbers) for subroutines
    variables = {}                 # maps variable name to its current value (int)

    lines = program.splitlines()
    i = 1                          # line numbers are 1-indexed
    labels = {}                    # name -> line number

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

        # CALL <name>
        elif cmd == 'CALL':
            if len(parts) < 2:
                raise ValueError(f"Line {i}: CALL requires an argument (e.g., CALL <name>)")
            name = parts[1]
            call_stack.append(i)          # push current line number as return address
            i = labels.get(name)          # jump to label
            if i is None:
                raise ValueError(f"Line {i}: Label '{name}' not defined")

        # RET
        elif cmd == 'RET':
            if len(call_stack) == 0:
                raise IndexError(f"Line {i}: No return address on call stack for RET at line {i}")
            ret_addr = call_stack.pop()   # pop the saved return line number
            i = ret_addr                  # jump to that line

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

        # EQ
        elif cmd == 'EQ':
            if len(parts) < 2:
                raise ValueError(f"Line {i}: EQ requires an argument (e.g., EQ)")
            a = stack.pop()
            b = stack.pop()   # note: pop order is b then a, but we need a and b for comparison
            if a == b:
                stack.append(1)
            else:
                stack.append(0)

        # GT
        elif cmd == 'GT':
            if len(parts) < 2:
                raise ValueError(f"Line {i}: GT requires an argument (e.g., GT)")
            a = stack.pop()
            b = stack.pop()
            if a > b:
                stack.append(1)
            else:
                stack.append(0)

        # LT
        elif cmd == 'LT':
            if len(parts) < 2:
                raise ValueError(f"Line {i}: LT requires an argument (e.g., LT)")
            a = stack.pop()
            b = stack.pop()
            if a < b:
                stack.append(1)
            else:
                stack.append(0)

        # STORE <var>
        elif cmd == 'STORE':
            if len(parts) < 2:
                raise ValueError(f"Line {i}: STORE requires an argument (e.g., STORE <var>)")
            var = parts[1]
            if not variables.get(var):
                raise ValueError(f"Line {i}: Variable '{var}' has not been stored yet")
            value = stack.pop()   # pop value to store
            variables[var] = value

        # LOAD <var>
        elif cmd == 'LOAD':
            if len(parts) < 2:
                raise ValueError(f"Line {i}: LOAD requires an argument (e.g., LOAD <var>)")
            var = parts[1]
            if var not in variables:
                raise ValueError(f"Line {i}: Variable '{var}' has not been stored yet")
            stack.append(variables[var])

        # DEFAULT unknown command
        else:
            raise ValueError(f"Unknown command '{cmd}' at line {i}")

        i += 1  # move to next line after processing a normal instruction

    return output
