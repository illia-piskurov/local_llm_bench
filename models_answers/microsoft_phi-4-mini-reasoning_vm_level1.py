def run(program):
    stack = []
    output = []
    lines = program.strip().split('\n')
    for line_no, line in enumerate(lines, start=1):
        stripped_line = line.strip()
        if not stripped_line or stripped_line.startswith('#'):
            continue
        parts = stripped_line.split()
        cmd = parts[0]
        args = parts[1:]
        
        try:
            if cmd == 'PUSH':
                n = int(args[0])
                stack.append(n)
            elif cmd == 'POP':
                if not stack:
                    raise Exception(f"Line {line_no}: POP on empty stack")
                output.append(str(stack.pop()))
            elif cmd in ['ADD', 'SUB', 'MUL', 'DIV']:
                if len(stack) < 2:
                    raise Exception(f"Line {line_no}: Insufficient elements for {cmd}")
                b = stack.pop()
                a = stack.pop()
                if cmd == 'ADD':
                    res = a + b
                elif cmd == 'SUB':
                    res = a - b
                else:  # MUL or DIV?
                    res = a * b
            elif cmd == 'DUP':
                if not stack:
                    raise Exception(f"Line {line_no}: DUP on empty stack")
                top = stack[-1]
                stack.append(top)
            elif cmd == 'SWAP':
                if len(stack) < 2:
                    raise Exception(f"Line {line_no}: SWAP requires at least two elements, but only {len(stack)} available.")
                a, b = stack[-1], stack[-2]
                stack[-2:] = [b, a]
            elif cmd == 'PRINT':
                if not stack:
                    raise Exception(f"Line {line_no}: PRINT on empty stack")
                output.append(str(stack[-1]))
            else:
                raise Exception(f"Line {line_no}: Unknown instruction '{cmd}'")
        except ValueError as ve:
            raise Exception(f"Line {line_no}: Invalid number in PUSH instruction") from ve
    return output

# Example usage (not part of the function to be tested)
if __name__ == "__main__":
    program = """
    # This is a comment
    PUSH 3
    DUP
    ADD
    PRINT
    """
    print(run(program))
