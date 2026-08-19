def run(program: str) -> list[str]:
    lines = [line.strip() for line in program.splitlines() if line.strip() and not line.strip().startswith("#")]
    stack = []
    call_stack = []
    variables = {}
    output = []

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
                    raise IndexError(f"Invalid jump to label '{parts[1]}' at line {i+1}")
                lines[i] = f"# JUMP TO LABEL {parts[1]} (replaced)"
            elif cmd == "JZ":
                if len(stack) < 1:
                    raise IndexError("Stack underflow for JZ at line {i+1}")
                val = stack.pop()
                target = labels[parts[1]]
                if not (0 <= target < len(lines)):
                    raise IndexError(f"Invalid jump to label '{parts[1]}' after JZ at line {i+1}")
                lines[i] = f"# JUMP TO LABEL {parts[1]} (replaced)"
                if val == 0:
                    i = target - 1
            elif cmd == "JNZ":
                if len(stack) < 1:
                    raise IndexError("Stack underflow for JNZ at line {i+1}")
                val = stack.pop()
                target = labels[parts[1]]
                if not (0 <= target < len(lines)):
                    raise IndexError(f"Invalid jump to label '{parts[1]}' after JNZ at line {i+1}")
                lines[i] = f"# JUMP TO LABEL {parts[1]} (replaced)"
                if val != 0:
                    i = target - 1
            elif cmd == "CALL":
                name = parts[1]
                call_stack.append((i + 1, len(stack)))
                for j in range(i + 1, len(lines)):
                    if lines[j].startswith("LABEL"):
                        label_name = lines[j].split()[1]
                        if label_name == name:
                            jmp_target = labels[label_name]
                            break
                    else:
                        continue
                    break
                else:
                    raise RuntimeError(f"Unmatched CALL to '{name}' at line {i+1}")
                i = jmp_target - 1
            elif cmd == "RET":
                if not call_stack:
                    raise RuntimeError("Ret without matching Call")
                ret_addr, prev_stack_len = call_stack.pop()
                stack.extend([0] * (len(stack) - prev_stack_len))
                i = ret_addr - 1
            elif cmd == "EQ":
                if len(stack) < 2:
                    raise IndexError(f"Not enough values on the stack for EQ at line {i+1}")
                b = stack.pop()
                a = stack.pop()
                stack.append(1 if a == b else 0)
            elif cmd == "GT":
                if len(stack) < 2:
                    raise IndexError(f"Not enough values on the stack for GT at line {i+1}")
                b = stack.pop()
                a = stack.pop()
                stack.append(1 if a > b else 0)
            elif cmd == "LT":
                if len(stack) < 2:
                    raise IndexError(f"Not enough values on the stack for LT at line {i+1}")
                b = stack.pop()
                a = stack.pop()
                stack.append(1 if a < b else 0)
            elif cmd.startswith("STORE"):
                var_name = parts[1]
                if not stack:
                    raise IndexError(f"Stack underflow for STORE '{var_name}' at line {i+1}")
                value = stack.pop()
                variables[var_name] = value
            elif cmd == "LOAD":
                var_name = parts[1]
                if var_name not in variables:
                    raise RuntimeError(f"Load of undefined variable '{var_name}'")
                stack.append(variables[var_name])
            else:
                raise ValueError(f"Unknown command '{cmd}' at line {i+1}")
        except (IndexError, ZeroDivisionError) as e:
            raise RuntimeError(f"Error at line {i+1}: {str(e)}")

    return output
