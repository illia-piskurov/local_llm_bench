def run(program: str) -> list[str]:
    stack = []
    lines = program.splitlines()
    for idx, raw in enumerate(lines):
        line_no = idx + 1
        stripped = raw.lstrip()
        if not stripped or stripped.startswith('#'):
            continue

        tokens = stripped.split()
        cmd = tokens[0]
        args = tokens[1:]

        try:
            if cmd == 'PUSH':
                n = int(args[0])
                stack.append(n)
            elif cmd == 'POP':
                if not stack:
                    raise ValueError(f'Line {line_no}: stack underflow')
                stack.pop()
            elif cmd == 'ADD':
                if len(stack) < 2:
                    raise ValueError(f'Line {line_no}: insufficient values for ADD')
                b = stack.pop()
                a = stack.pop()
                stack.append(a + b)
            elif cmd == 'SUB':
                if len(stack) < 2:
                    raise ValueError(f'Line {line_no}: insufficient values for SUB')
                b = stack.pop()
                a = stack.pop()
                stack.append(a - b)
            elif cmd == 'MUL':
                if len(stack) < 2:
                    raise ValueError(f'Line {line_no}: insufficient values for MUL')
                b = stack.pop()
                a = stack.pop()
                stack.append(a * b)
            elif cmd == 'DIV':
                if len(stack) < 2:
                    raise ValueError(f'Line {line_no}: insufficient values for DIV')
                b = stack.pop()
                if b == 0:
                    raise ValueError(f'Line {line_no}: division by zero')
                a = stack.pop()
                stack.append(a // b)
            elif cmd == 'DUP':
                if not stack:
                    raise ValueError(f'Line {line_no}: stack underflow for DUP')
                stack.append(stack[-1])
            elif cmd == 'SWAP':
                if len(stack) < 2:
                    raise ValueError(f'Line {line_no}: insufficient values for SWAP')
                top = stack.pop()
                second = stack.pop()
                stack.append(top)
                stack.append(second)
            elif cmd == 'PRINT':
                if not stack:
                    raise ValueError(f'Line {line_no}: stack underflow for PRINT')
                output.append(stack[-1])
            else:
                raise ValueError(f'Line {line_no}: unknown instruction "{cmd}"')
        except Exception as e:
            # Re-raise with line number info
            raise ValueError(str(e)) from None

    return output
