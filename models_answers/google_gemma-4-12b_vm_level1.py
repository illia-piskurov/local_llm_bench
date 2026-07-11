def run(program: str) -> list[str]:
    stack = []
    output = []
    lines = program.splitlines()

    for i, line in enumerate(lines):
        line_num = i + 1
        stripped = line.strip()
        # Skip empty lines and comments
        if not stripped or stripped.startswith('#'):
            continue
        
        parts = stripped.split()
        if not parts:
            continue
            
        cmd = parts[0].upper()

        if cmd == "PUSH":
            try:
                stack.append(int(parts[1]))
            except (IndexError, ValueError):
                pass # Or handle as error if input is guaranteed to be valid
        elif cmd == "POP":
            if len(stack) < 1:
                raise ValueError(f"Line {line_num}: Stack underflow")
            stack.pop()
        elif cmd == "ADD":
            if len(stack) < 2:
                raise ValueError(f"Line {line_num}: Stack underflow")
            b = stack.pop()
            a = stack.pop()
            stack.append(a + b)
        elif cmd == "SUB":
            if len(stack) < 2:
                raise ValueError(f"Line {line_num}: Stack underflow")
            b = stack.pop()
            a = stack.pop()
            stack.append(a - b)
        elif cmd == "MUL":
            if len(stack) < 2:
                raise ValueError(f"Line {line_num}: Stack underflow")
            b = stack.pop()
            a = stack.pop()
            stack.append(a * b)
        elif cmd == "DIV":
            if len(stack) < 2:
                raise ValueError(f"Line {line_num}: Stack underflow")
            b = stack.pop()
            a = stack.pop()
            if b == 0:
                raise ValueError(f"Line {line_num}: Division by zero")
            stack.append(a // b)
        elif cmd == "DUP":
            if len(stack) < 1:
                raise ValueError(f"Line {line_num}: Stack underflow")
            stack.append(stack[-1])
        elif cmd == "SWAP":
            if len(stack) < 2:
                raise ValueError(f"Line {line_num}: Stack underflow")
            a = stack.pop()
            b = stack.pop()
            stack.append(a)
            stack.append(b)
        elif cmd == "PRINT":
            if len(stack) < 1:
                raise ValueError(f"Line {line_num}: Stack underflow")
            output.append(str(stack[-1]))

    return output
