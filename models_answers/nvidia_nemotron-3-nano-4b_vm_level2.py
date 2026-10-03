def run(program: str) -> list[str]:
    lines = program.splitlines()
    stack = []
    output = []
    label_map = {}

    for idx, line in enumerate(lines):
        line = line.strip()
        if not line or line.startswith('#'):
            continue

        tokens = line.split()
        op = tokens[0]

        # LABEL
        if op == 'LABEL':
            name = tokens[1]
            label_map[name] = idx + 1
            continue

        # JMP, JZ, JNZ
        elif op == 'JMP':
            target = tokens[1]
            if target not in label_map:
                raise ValueError(f"Line {idx+1}: undefined label '{target}'")
            idx = label_map[target]  # jump to this line (loop will continue after it)
            continue
        elif op == 'JZ':
            if len(tokens) != 2:
                raise ValueError(f"Line {idx+1}: JZ expects one value, got {len(stack)}")
            v = stack.pop()
            if v != 0:                     # not zero → no jump
                continue
            target = tokens[1]
            if target not in label_map:
                raise ValueError(f"Line {idx+1}: undefined label '{target}'")
            idx = label_map[target]        # jump to this line
            continue
        elif op == 'JNZ':
            if len(tokens) != 2:
                raise ValueError(f"Line {idx+1}: JNZ expects one value, got {len(stack)}")
            v = stack.pop()
            if v == 0:                     # zero → no jump
                continue
            target = tokens[1]
            if target not in label_map:
                raise ValueError(f"Line {idx+1}: undefined label '{target}'")
            idx = label_map[target]        # jump to this line
            continue

        # Existing instructions (unchanged)
        elif op == 'PUSH':
            n = int(tokens[1])
            stack.append(n)

        elif op == 'POP':
            if not stack:
                raise ValueError(f"Line {idx+1}: POP on empty stack")
            stack.pop()

        elif op == 'ADD':
            if len(stack) < 2:
                raise ValueError(f"Line {idx+1}: ADD requires two values, got {len(stack)}")
            b = stack.pop()
            a = stack.pop()
            stack.append(a + b)

        elif op == 'SUB':
            if len(stack) < 2:
                raise ValueError(f"Line {idx+1}: SUB requires two values, got {len(stack)}")
            b = stack.pop()
            a = stack.pop()
            stack.append(a - b)

        elif op == 'MUL':
            if len(stack) < 2:
                raise ValueError(f"Line {idx+1}: MUL requires two values, got {len(stack)}")
            b = stack.pop()
            a = stack.pop()
            stack.append(a * b)

        elif op == 'DIV':
            if len(stack) < 2:
                raise ValueError(f"Line {idx+1}: DIV requires two values, got {len(stack)}")
            b = stack.pop()
            a = stack.pop()
            if b == 0:
                raise ValueError(f"Line {idx+1}: division by zero")
            stack.append(a // b)

        elif op == 'DUP':
            if not stack:
                raise ValueError(f"Line {idx+1}: DUP on empty stack")
            stack.append(stack[-1])

        elif op == 'SWAP':
            if len(stack) < 2:
                raise ValueError(f"Line {idx+1}: SWAP requires two values, got {len(stack)}")
            a = stack.pop()
            b = stack.pop()
            stack.append(a)
            stack.append(b)

        elif op == 'PRINT':
            if not stack:
                raise ValueError(f"Line {idx+1}: PRINT on empty stack")
            output.append(str(stack[-1]))

        else:
            raise ValueError(f"Line {idx+1}: unknown instruction '{op}'")

    return output
