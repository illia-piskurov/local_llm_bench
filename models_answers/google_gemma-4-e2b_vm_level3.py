def run(program: str) -> list[str]:
    """
    Interprets a stack-based program and returns a list of printed output strings,
    supporting conditional jumps, labels, subroutines, comparisons, and named variables.
    """
    lines = program.strip().split('\n')
    stack = []
    output = []
    labels = {}
    variables = {}  # Dictionary to simulate memory/variables
    call_stack = [] # Stack for subroutine return addresses (markers)

    i = 0
    while i < len(lines):
        line_num = i + 1
        raw_line = lines[i]
        
        # Clean the line: remove leading/trailing whitespace and ignore comments/empty lines
        line = raw_line.strip()

        if not line or line.startswith("#"):
            i += 1
            continue

        parts = line.split()
        if not parts:
            i += 1
            continue

        instruction = parts[0].upper()

        try:
            if instruction == "PUSH":
                if len(parts) != 2:
                    raise ValueError("PUSH requires one argument (number).")
                value = int(parts[1])
                stack.append(value)

            elif instruction == "POP":
                if not stack:
                    raise IndexError(f"POP failed: Stack is empty at line {line_num}.")
                stack.pop()

            elif instruction == "ADD":
                if len(stack) < 2:
                    raise IndexError(f"ADD failed: Not enough operands. Stack size is {len(stack)} at line {line_num}.")
                b = stack.pop()
                a = stack.pop()
                stack.append(a + b)

            elif instruction == "SUB":
                if len(stack) < 2:
                    raise IndexError(f"SUB failed: Not enough operands. Stack size is {len(stack)} at line {line_num}.")
                b = stack.pop()  # b is the subtrahend
                a = stack.pop()  # a is the minuend
                stack.append(a - b)

            elif instruction == "MUL":
                if len(stack) < 2:
                    raise IndexError(f"MUL failed: Not enough operands. Stack size is {len(stack)} at line {line_num}.")
                b = stack.pop()
                a = stack.pop()
                stack.append(a * b)

            elif instruction == "DIV":
                if len(stack) < 2:
                    raise IndexError(f"DIV failed: Not enough operands. Stack size is {len(stack)} at line {line_num}.")
                b = stack.pop()  # Divisor
                a = stack.pop()  # Dividend

                if b == 0:
                    raise ZeroDivisionError(f"DIV failed: Division by zero at line {line_num}.")
                
                # Integer division
                result = int(a / b) 
                stack.append(result)

            elif instruction == "DUP":
                if not stack:
                    raise IndexError(f"DUP failed: Stack is empty at line {line_num}.")
                top = stack[-1]
                stack.append(top)
                stack.append(top)

            elif instruction == "SWAP":
                if len(stack) < 2:
                    raise IndexError(f"SWAP failed: Not enough operands. Stack size is {len(stack)} at line {line_num}.")
                b = stack.pop()
                a = stack.pop()
                stack.append(b)
                stack.append(a)

            elif instruction == "PRINT":
                if not stack:
                    raise IndexError(f"PRINT failed: Stack is empty at line {line_num}.")
                value = stack.pop()
                output.append(str(value))

            # --- New Instructions Start Here ---

            elif instruction == "LABEL":
                if len(parts) != 2:
                    raise ValueError("LABEL requires one argument (name).")
                label_name = parts[1]
                labels[line_num] = label_name

            elif instruction == "JMP":
                if len(parts) != 2:
                    raise ValueError("JMP requires one argument (label name).")
                target_label = parts[1]
                
                if target_label not in labels:
                    raise NameError(f"JMP failed: Label '{target_label}' not defined.")
                
                # Jump implementation
                target_index = -1
                for k, v in labels.items():
                    if v == target_label:
                        target_index = k
                        break

                if target_index != -1:
                    i = target_index
                    continue 
                else:
                     raise NameError(f"JMP failed: Label '{target_label}' not found.")


            elif instruction == "JZ":
                if len(parts) != 2:
                    raise ValueError("JZ requires one argument (label name).")
                target_label = parts[1]

                if not stack:
                    raise IndexError(f"JZ failed: Stack is empty at line {line_num}.")

                value = stack.pop()
                if value == 0:
                    # Jump implementation
                    target_index = -1
                    for k, v in labels.items():
                        if v == target_label:
                            target_index = k
                            break
                    if target_index != -1:
                        i = target_index
                        continue 

            elif instruction == "JNZ":
                if len(parts) != 2:
                    raise ValueError("JNZ requires one argument (label name).")
                target_label = parts[1]

                if not stack:
                    raise IndexError(f"JNZ failed: Stack is empty at line {line_num}.")
                
                value = stack.pop()
                if value != 0:
                    # Jump implementation
                    target_index = -1
                    for k, v in labels.items():
                        if v == target_label:
                            target_index = k
                            break
                    if target_index != -1:
                        i = target_index
                        continue 

            # --- Subroutine/Memory Instructions ---
            
            elif instruction == "CALL":
                if len(parts) != 2:
                    raise ValueError("CALL requires one argument (label name).")
                target_label = parts[1]

                if target_label not in labels:
                    raise NameError(f"CALL failed: Label '{target_label}' not defined.")

                # Push current instruction pointer (i) onto call stack
                call_stack.append(i)

                # Jump implementation
                target_index = -1
                for k, v in labels.items():
                    if v == target_label:
                        target_index = k
                        break

                if target_index != -1:
                    i = target_index
                    continue
                else:
                     raise NameError(f"CALL failed: Label '{target_label}' not found.")

            elif instruction == "RET":
                if not call_stack:
                    raise IndexError("RET failed: Call stack is empty.")
                
                # Pop return address
                return_index = call_stack.pop()
                
                # Set instruction pointer to the return address and continue (skip i+=1)
                i = return_index 
                continue

            elif instruction == "EQ":
                if len(stack) < 2:
                    raise IndexError(f"EQ failed: Not enough operands. Stack size is {len(stack)} at line {line_num}.")
                b = stack.pop()
                a = stack.pop()
                stack.append(1 if a == b else 0)

            elif instruction == "GT":
                if len(stack) < 2:
                    raise IndexError(f"GT failed: Not enough operands. Stack size is {len(stack)} at line {line_num}.")
                b = stack.pop()
                a = stack.pop()
                stack.append(1 if a > b else 0)

            elif instruction == "LT":
                if len(stack) < 2:
                    raise IndexError(f"LT failed: Not enough operands. Stack size is {len(stack)} at line {line_num}.")
                b = stack.pop()
                a = stack.pop()
                stack.append(1 if a < b else 0)

            elif instruction == "STORE":
                if not stack:
                    raise IndexError(f"STORE failed: Stack is empty at line {line_num}.")
                value = stack.pop()
                var_name = parts[1]
                variables[var_name] = value

            elif instruction == "LOAD":
                if len(parts) != 2:
                    raise ValueError("LOAD requires one argument (variable name).")
                var_name = parts[1]

                if var_name not in variables:
                    raise NameError(f"LOAD failed: Variable '{var_name}' not defined or stored.")
                
                value = variables[var_name]
                stack.append(value)

            else:
                raise ValueError(f"Unknown instruction '{instruction}' at line {line_num}.")

        except (IndexError, ValueError, ZeroDivisionError, NameError) as e:
            # Re-raise relevant errors found during execution
            raise e
        
        i += 1

    return output
