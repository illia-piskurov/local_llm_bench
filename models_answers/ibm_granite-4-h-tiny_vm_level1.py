def run(program: str) -> list[str]:
    lines = [line.strip() for line in program.splitlines() if line.strip() and not line.strip().startswith("#")]
    stack = []
    output = []
    line_number = 0

    def error(msg):
        raise ValueError(f"Error at line {line_number}: {msg}")

    for line in lines:
        line_number += 1
        parts = line.split()
        cmd = parts[0]

        try:
            if cmd == "PUSH":
                value = int(parts[1])
                stack.append(value)
            elif cmd == "POP":
                if not stack:
                    error("stack underflow")
                stack.pop()
            elif cmd == "ADD":
                if len(stack) < 2:
                    error("not enough values on the stack for ADD")
                a, b = stack.pop(), stack.pop()
                stack.append(a + b)
            elif cmd == "SUB":
                if len(stack) < 2:
                    error("not enough values on the stack for SUB")
                a, b = stack.pop(), stack.pop()
                stack.append(b - a)  # ensure correct order
            elif cmd == "MUL":
                if len(stack) < 2:
                    error("not enough values on the stack for MUL")
                a, b = stack.pop(), stack.pop()
                stack.append(a * b)
            elif cmd == "DIV":
                if len(stack) < 2:
                    error("not enough values on the stack for DIV")
                a, b = stack.pop(), stack.pop()
                if b == 0:
                    error("division by zero")
                stack.append(b // a)
            elif cmd == "DUP":
                if not stack:
                    error("stack underflow")
                stack.append(stack[-1])
            elif cmd == "SWAP":
                if len(stack) < 2:
                    error("not enough values on the stack for SWAP")
                stack[-1], stack[-2] = stack[-2], stack[-1]
            elif cmd == "PRINT":
                if not stack:
                    error("stack underflow")
                output.append(str(stack[-1]))
            else:
                error(f"unknown command: {cmd}")
        except (IndexError, ValueError) as e:
            raise ValueError(f"Syntax or value error at line {line_number}: {e}")

    return output
