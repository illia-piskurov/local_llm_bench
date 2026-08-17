def run(program: str) -> list[str]:
    stack = []
    output = []
    lines = program.splitlines()
    
    # Pre-process: parse instructions and find labels
    # instructions will store (original_line_number, command, args)
    instructions = []
    labels = {}
    
    for line_idx, raw_line in enumerate(lines, 1):
        line = raw_line.strip()
        if not line or line.startswith('#'):
            continue
        
        parts = line.split()
        command = parts[0].upper()
        args = parts[1:]
        
        if command == "LABEL":
            if not args:
                raise RuntimeError(f"Error at line {line_idx}: LABEL requires a name")
            label_name = args[0]
            if label_name in labels:
                raise RuntimeError(f"Error at line {line_idx}: Duplicate label '{label_name}'")
            labels[label_name] = len(instructions)
            # We add LABEL as a dummy instruction so the index matches
            instructions.append((line_idx, "LABEL", []))
        else:
            instructions.append((line_idx, command, args))

    ip = 0  # Instruction pointer
    while ip < len(instructions):
        line_idx, command, args = instructions[ip]
        
        try:
            if command == "PUSH":
                if not args:
                    raise ValueError("PUSH requires an argument")
                stack.append(int(args[0]))
                ip += 1

            elif command == "POP":
                if len(stack) < 1:
                    raise IndexError("Stack underflow: cannot POP from empty stack")
                stack.pop()
                ip += 1

            elif command == "ADD":
                if len(stack) < 2:
                    raise IndexError("Stack underflow: ADD requires 2 values")
                b = stack.pop()
                a = stack.pop()
                stack.append(a + b)
                ip += 1

            elif command == "SUB":
                if len(stack) < 2:
                    raise IndexError("Stack underflow: SUB requires 2 values")
                b = stack.pop()
                a = stack.pop()
                stack.append(a - b)
                ip += 1

            elif command == "MUL":
                if len(stack) < 2:
                    raise IndexError("Stack underflow: MUL requires 2 values")
                b = stack.pop()
                a = stack.pop()
                stack.append(a * b)
                ip += 1

            elif command == "DIV":
                if len(stack) < 2:
                    raise IndexError("Stack underflow: DIV requires 2 values")
                b = stack.pop()
                a = stack.pop()
                if b == 0:
                    raise ZeroDivisionError("Division by zero")
                stack.append(a // b)
                ip += 1

            elif command == "DUP":
                if len(stack) < 1:
                    raise IndexError("Stack underflow: DUP requires 1 value")
                stack.append(stack[-1])
                ip += 1

            elif command == "SWAP":
                if len(stack) < 2:
                    raise IndexError("Stack underflow: SWAP requires 2 values")
                stack[-1], stack[-2] = stack[-2], stack[-1]
                ip += 1

            elif command == "PRINT":
                if len(stack) < 1:
                    raise IndexError("Stack underflow: PRINT requires 1 value")
                output.append(str(stack[-1]))
                ip += 1

            elif command == "LABEL":
                # Label is a no-op, just move to next instruction
                ip += 1

            elif command == "JMP":
                if not args:
                    raise ValueError("JMP requires a label name")
                label_name = args[0]
                if label_name not in labels:
                    raise ValueError(f"Undefined label: {label_name}")
                ip = labels[label_name]

            elif command == "JZ":
                if not args:
                    raise ValueError("JZ requires a label name")
                label_name = args[0]
                if label_name not in labels:
                    raise ValueError(f"Undefined label: {label_name}")
                if len(stack) < 1:
                    raise IndexError("Stack underflow: JZ requires 1 value")
                val = stack.pop()
                if val == 0:
                    ip = labels[label_name]
                else:
                    ip += 1

            elif command == "JNZ":
                if not args:
                    raise ValueError("JNZ requires a label name")
                label_name = args[0]
                if label_name not in labels:
                    raise ValueError(f"Undefined label: {label_name}")
                if len(stack) < 1:
                    raise IndexError("Stack underflow: JNZ requires 1 value")
                val = stack.pop()
                if val != 0:
                    ip = labels[label_name]
                else:
                    ip += 1

            else:
                raise ValueError(f"Unknown command: {command}")

        except (IndexError, ZeroDivisionError, ValueError) as e:
            error_msg = str(e)
            if "Stack underflow" in error_msg:
                raise RuntimeError(f"Error at line {line_idx}: {error_msg}")
            elif "Division by zero" in error_msg:
                raise RuntimeError(f"Error at line {line_idx}: Division by zero")
            else:
                raise RuntimeError(f"Error at line {line_idx}: {error_msg}")

    return output

if __name__ == "__main__":
    # Test with loops
    code = """
    PUSH 5
    LABEL loop
    PRINT
    PUSH 1
    SUB
    DUP
    JZ end
    JMP loop
    LABEL end
    """
    try:
        results = run(code)
        for res in results:
            print(res)
    except RuntimeError as e:
        print(e)
