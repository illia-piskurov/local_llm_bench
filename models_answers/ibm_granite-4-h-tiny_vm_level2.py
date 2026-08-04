def run(program: str) -> list[str]:
    lines = [line.strip() for line in program.splitlines() if line.strip() and not line.strip().startswith("#")]
    stack = []
    output = []
    labels = {}

    label_index = 0
    for i, line in enumerate(lines):
        parts = line.split()
        cmd = parts[0]

        try:
            if cmd == "PUSH":
                n = int(parts[1])
                stack.append(n)
            elif cmd == "POP":
                if not stack:
                    raise IndexError(f"Stack underflow at line {i+1}")
                stack.pop()
            elif cmd == "ADD":
                if len(stack) < 2:
                    raise IndexError(f"Not enough values on the stack for ADD at line {i+1}")
                b = stack.pop()
                a = stack.pop()
                stack.append(a + b)
            elif cmd == "SUB":
                if len(stack) < 2:
                    raise IndexError(f"Not enough values on the stack for SUB at line {i+1}")
                b = stack.pop()
                a = stack.pop()
                stack.append(a - b)
            elif cmd == "MUL":
                if len(stack) < 2:
                    raise IndexError(f"Not enough values on the stack for MUL at line {i+1}")
                b = stack.pop()
                a = stack.pop()
                stack.append(a * b)
            elif cmd == "DIV":
                if len(stack) < 2:
                    raise IndexError(f"Not enough values on the stack for DIV at line {i+1}")
                b = stack.pop()
                a = stack.pop()
                if b == 0:
                    raise ZeroDivisionError(f"Division by zero at line {i+1}")
                stack.append(a // b)
            elif cmd == "DUP":
                if not stack:
                    raise IndexError("Stack underflow for DUP at line {i+1}")
                stack.append(stack[-1])
            elif cmd == "SWAP":
                if len(stack) < 2:
                    raise IndexError(f"Not enough values on the stack for SWAP at line {i+1}")
                a = stack.pop()
                b = stack.pop()
                stack.append(a)
                stack.append(b)
            elif cmd == "PRINT":
                if not stack:
                    raise IndexError("Stack underflow for PRINT at line {i+1}")
                output.append(str(stack[-1]))
            elif cmd.startswith("LABEL"):
                name = parts[1]
                labels[name] = i
            elif cmd == "JMP":
                target = labels[parts[1]]
                if not (0 <= target < len(lines)):
                    raise IndexError(f"Label '{parts[1]}' not found at line {i+1}")
                lines[i] = f"# JUMP TO LABEL {parts[1]} (replaced)"
            elif cmd == "JZ":
                if len(stack) < 1:
                    raise IndexError("Stack underflow for JZ at line {i+1}")
                val = stack.pop()
                target = labels[parts[1]]
                if not (0 <= target < len(lines)):
                    raise IndexError(f"Label '{parts[1]}' not found at line {i+1}")
                lines[i] = f"# JMP TO LABEL {parts[1]} (replaced)"
                if val == 0:
                    i = target - 1
            elif cmd == "JNZ":
                if len(stack) < 1:
                    raise IndexError("Stack underflow for JNZ at line {i+1}")
                val = stack.pop()
                target = labels[parts[1]]
                if not (0 <= target < len(lines)):
                    raise IndexError(f"Label '{parts[1]}' not found at line {i+1}")
                lines[i] = f"# JMP TO LABEL {parts[1]} (replaced)"
                if val != 0:
                    i = target - 1
            else:
                raise ValueError(f"Unknown command '{cmd}' at line {i+1}")
        except (IndexError, ZeroDivisionError) as e:
            raise RuntimeError(f"Error at line {i+1}: {str(e)}")

    return output
