def run(program: str) -> list[str]:
    lines = [line.strip() for line in program.splitlines() if line.strip() and not line.strip().startswith("#")]
    stack = []
    call_stack = []
    memory = {}
    output = []

    def error(msg):
        raise ValueError(f"Error at line {len(output)+1}: {msg}")

    label_map = {}

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
        elif cmd.startswith("LABEL"):
            try:
                label_name = parts[1]
                labels[label_name] = i
            except (IndexError, ValueError):
                error("Invalid LABEL format")
        elif cmd == "JMP":
            if len(parts) != 2:
                error("JMP requires a label argument")
            target_line = labels.get(parts[1])
            if target_line is None:
                error(f"Undefined label: {parts[1]}")
            i = target_line
        elif cmd == "JZ":
            if len(parts) != 2:
                error("JZ requires a label argument")
            try:
                value = int(stack.pop())
            except (IndexError, ValueError):
                error("Invalid value for JZ")
            target_line = labels.get(parts[1])
            if target_line is None:
                error(f"Undefined label: {parts[1]}")
            if value == 0:
                i = target_line
        elif cmd == "JNZ":
            if len(parts) != 2:
                error("JNZ requires a label argument")
            try:
                value = int(stack.pop())
            except (IndexError, ValueError):
                error("Invalid value for JNZ")
            target_line = labels.get(parts[1])
            if target_line is None:
                error(f"Undefined label: {parts[1]}")
            if value != 0:
                i = target_line
        elif cmd == "CALL":
            if len(parts) != 2:
                error("CALL requires a label argument")
            call_stack.append(i + 1)
            try:
                label_name = parts[1]
                labels[label_name] = i
            except (IndexError, ValueError):
                error("Invalid CALL format")
        elif cmd == "RET":
            if not call_stack:
                error("RET on empty call stack")
            i = call_stack.pop()
        elif cmd == "EQ":
            if len(stack) < 2:
                error("EQ requires two values on the stack")
            b = stack.pop()
            a = stack.pop()
            stack.append(1 if a == b else 0)
        elif cmd == "GT":
            if len(stack) < 2:
                error("GT requires two values on the stack")
            b = stack.pop()
            a = stack.pop()
            stack.append(1 if a > b else 0)
        elif cmd == "LT":
            if len(stack) < 2:
                error("LT requires two values on the stack")
            b = stack.pop()
            a = stack.pop()
            stack.append(1 if a < b else 0)
        elif cmd.startswith("STORE"):
            try:
                var_name = parts[1]
                value = stack.pop()
                memory[var_name] = value
            except (IndexError, ValueError):
                error("Invalid STORE format")
        elif cmd == "LOAD":
            try:
                var_name = parts[1]
                if var_name not in memory:
                    error(f"Undefined variable: {var_name}")
                stack.append(memory[var_name])
            except (IndexError, ValueError):
                error("Invalid LOAD format")
        else:
            raise ValueError(f"Unknown command: {cmd}")

    return output
