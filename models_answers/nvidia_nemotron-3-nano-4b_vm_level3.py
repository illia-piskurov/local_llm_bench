def run(program: str) -> list[str]:
    lines = program.splitlines()
    stack = []
    output = []

    # Build label map while parsing (ignoring comments/empty)
    label_map = {}
    for idx, raw in enumerate(lines):
        line = raw.strip()
        if not line or line.startswith('#'):
            continue
        tokens = line.split()
        cmd = tokens[0]
        if cmd == 'LABEL':
            label_map[tokens[1]] = idx

    i = 0
    call_stack = []
    var_store = {}

    while i < len(lines):
        raw = lines[i]
        line = raw.strip()
        if not line or line.startswith('#'):
            i += 1
            continue

        tokens = line.split()
        cmd = tokens[0]

        # LABEL – just record (already done) and move on
        if cmd == 'LABEL':
            i += 1
            continue

        # CALL / RET – handle jumps and call stack
        elif cmd == 'CALL':
            target = tokens[1]
            if target not in label_map:
                raise Exception(f'Label "{target}" not defined at line {i}')
            call_stack.append(i)
            i = label_map[target] - 1
            continue

        elif cmd == 'RET':
            if not call_stack:
                raise Exception('Stack of calls is empty at RET')
            address = call_stack.pop()
            i = address - 1
            continue

        # EQ / GT / LT – compare ops
        elif cmd == 'EQ':
            if len(stack) < 2:
                raise Exception(f'Stack underflow at line {i}')
            b = stack.pop()
            a = stack.pop()
            stack.append(1 if a == b else 0)

        elif cmd == 'GT':
            if len(stack) < 2:
                raise Exception(f'Stack underflow at line {i}')
            b = stack.pop()
            a = stack.pop()
            stack.append(1 if a > b else 0)

        elif cmd == 'LT':
            if len(stack) < 2:
                raise Exception(f'Stack underflow at line {i}')
            b = stack.pop()
            a = stack.pop()
            stack.append(1 if a < b else 0)

        # STORE / LOAD – named variables
        elif cmd == 'STORE':
            if not stack:
                raise Exception(f'Stack underflow at line {i}')
            val = stack.pop()
            var_name = tokens[1]
            var_store[var_name] = val

        elif cmd == 'LOAD':
            var_name = tokens[1]
            if var_name not in var_store:
                raise Exception(f'Variable "{var_name}" not defined at line {i}')
            stack.append(var_store[var_name])

        # Existing stack operations (PUSH, POP, ADD, SUB, MUL, DIV, DUP, SWAP)
        elif cmd == 'PUSH':
            n = int(tokens[1])
            stack.append(n)

        elif cmd == 'POP':
            if not stack:
                raise Exception(f'Stack underflow at line {i}')
            stack.pop()

        elif cmd == 'ADD':
            if len(stack) < 2:
                raise Exception(f'Stack underflow at line {i}')
            b = stack.pop()
            a = stack.pop()
            stack.append(a + b)

        elif cmd == 'SUB':
            if len(stack) < 2:
                raise Exception(f'Stack underflow at line {i}')
            b = stack.pop()
            a = stack.pop()
            stack.append(a - b)

        elif cmd == 'MUL':
            if len(stack) < 2:
                raise Exception(f'Stack underflow at line {i}')
            b = stack.pop()
            a = stack.pop()
            stack.append(a * b)

        elif cmd == 'DIV':
            if len(stack) < 2:
                raise Exception(f'Stack underflow at line {i}')
            b = stack.pop()
            a = stack.pop()
            if b == 0:
                raise Exception(f'Division by zero at line {i}')
            stack.append(a // b)

        elif cmd == 'DUP':
            if not stack:
                raise Exception(f'Stack underflow at line {i}')
            stack.append(stack[-1])

        elif cmd == 'SWAP':
            if len(stack) < 2:
                raise Exception(f'Stack underflow at line {i}')
            a = stack.pop()
            b = stack.pop()
            stack.append(a)
            stack.append(b)

        # PRINT
        elif cmd == 'PRINT':
            output.append(str(stack[-1]))

        else:
            raise Exception(f'Unknown command "{cmd}" at line {i}')

        i += 1

    return output
