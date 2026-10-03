def run(program: str) -> list[str]:
    lines = [line.strip() for line in program.splitlines() if line.strip() and not line.strip().startswith("#")]
    stack = []
    output = []

    def error(msg):
        raise ValueError(f"Error at line {len(output)+1}: {msg}")

    for i, line in enumerate(lines, start=1):
        parts = line.split()
        cmd = parts[0]
        if cmd == "PUSH":
            try:
                value = int(parts[1])
            except (IndexError, ValueError):
                error("Missing number after PUSH")
            stack.append(value)
        elif cmd == "POP":
            if not stack:
                error("POP from empty stack")
            stack.pop()
        elif cmd == "ADD":
            if len(stack) < 2:
                error("ADD requires two values on the stack")
            b = stack.pop()
            a = stack.pop()
            stack.append(a + b)
        elif cmd == "SUB":
            if len(stack) < 2:
                error("SUB requires two values on the stack")
            b = stack.pop()
            a = stack.pop()
            stack.append(a - b)
        elif cmd == "MUL":
            if len(stack) < 2:
                error("MUL requires two values on the stack")
            b = stack.pop()
            a = stack.pop()
            stack.append(a * b)
        elif cmd == "DIV":
            if len(stack) < 2:
                error("DIV requires two values on the stack")
            b = stack.pop()
            a = stack.pop()
            if b == 0:
                error("Division by zero")
            stack.append(a // b)
        elif cmd == "DUP":
            if not stack:
                error("DUP from empty stack")
            stack.append(stack[-1])
        elif cmd == "SWAP":
            if len(stack) < 2:
                error("SWAP requires two values on the stack")
            stack[-1], stack[-2] = stack[-2], stack[-1]
        elif cmd == "PRINT":
            if not stack:
                error("PRINT from empty stack")
            output.append(str(stack[-1]))
        else:
            raise ValueError(f"Unknown command: {cmd}")

    return output
