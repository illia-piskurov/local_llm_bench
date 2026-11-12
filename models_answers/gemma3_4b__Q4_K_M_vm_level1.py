def run(program: str) -> list[str]:
    """
    Interprets a simple stack-based language and returns a list of printed strings.
    """
    stack = []
    printed = []
    lines = program.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line or line.startswith("#"):
            i += 1
            continue

        parts = line.split()
        instruction = parts[0]

        if instruction == "PUSH":
            try:
                value = int(parts[1])
                stack.append(value)
            except (IndexError, ValueError):
                raise ValueError(f"Invalid PUSH instruction: {line} (expected <n>")
        elif instruction == "POP":
            if not stack:
                raise ValueError(f"Stack underflow: POP (line {i+1})")
            stack.pop()
        elif instruction == "ADD":
            if len(stack) < 2:
                raise ValueError(f"Stack underflow: ADD (line {i+1})")
            val2 = stack.pop()
            val1 = stack.pop()
            stack.append(val1 + val2)
        elif instruction == "SUB":
            if len(stack) < 2:
                raise ValueError(f"Stack underflow: SUB (line {i+1})")
            val2 = stack.pop()
            val1 = stack.pop()
            stack.append(val1 - val2)
        elif instruction == "MUL":
            if len(stack) < 2:
                raise ValueError(f"Stack underflow: MUL (line {i+1})")
            val2 = stack.pop()
            val1 = stack.pop()
            stack.append(val1 * val2)
        elif instruction == "DIV":
            if len(stack) < 2:
                raise ValueError(f"Stack underflow: DIV (line {i+1})")
            val2 = stack.pop()
            val1 = stack.pop()
            if val2 == 0:
                raise ZeroDivisionError(f"Division by zero (line {i+1})")
            stack.append(val1 // val2)
        elif instruction == "DUP":
            if not stack:
                raise ValueError(f"Stack underflow: DUP (line {i+1})")
            top = stack[-1]
            stack.append(top)
        elif instruction == "SWAP":
            if len(stack) < 2:
                raise ValueError(f"Stack underflow: SWAP (line {i+1})")
            val2 = stack.pop()
            val1 = stack.pop()
            stack.append(val1)
            stack.append(val2)
        elif instruction == "PRINT":
            if not stack:
                print("Stack is empty")
            else:
                print(stack[-1])
        else:
            raise ValueError(f"Invalid instruction: {instruction} (line {i+1})")

        i += 1
    return printed
