import re

def run(program: str) -> list[str]:
    """
    Runs the stack-based program and returns a list of printed strings.
    Supports labels, conditional jumps, subroutines, comparisons, and variables.
    Raises an exception on runtime error (stack underflow, division by zero, etc.).
    """
    stack = []
    output = []
    memory = {}  # Named variable storage
    call_stack = [] # Return addresses for CALL/RET

    lines = [line.strip() for line in program.split('\n')]

    # --- Phase 1: Pre-process Labels ---
    label_map = {}
    for i, raw_line in enumerate(lines):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        parts = line.split()
        if parts and parts[0] == "LABEL":
            label_name = parts[1]
            # Store the program counter index (i) for this label
            label_map[label_name] = i

    # --- Phase 2: Execution ---
    program_counter = 0
    max_lines = len(lines)

    while program_counter < max_lines:
        line = lines[program_counter]
        if not line or line.startswith("#"):
            program_counter += 1
            continue

        parts = line.split()
        command = parts[0]
        args = parts[1:]
        line_num = program_counter + 1 # Current instruction's line number

        try:
            if command == "LABEL":
                pass

            # --- Data Manipulation ---
            elif command == "PUSH":
                if args and args[0].isdigit():
                    stack.append(int(args[0]))
                else:
                    raise ValueError("PUSH requires a valid integer argument.")

            elif command == "POP":
                if not stack:
                    raise IndexError("Stack underflow: Cannot POP from an empty stack.")
                stack.pop()

            # --- Arithmetic Operations ---
            elif command == "ADD":
                if len(stack) < 2:
                    raise IndexError("Stack underflow: ADD requires at least two values.")
                b = stack.pop()
                a = stack.pop()
                stack.append(a + b)

            elif command == "SUB":
                if len(stack) < 2:
                    raise IndexError("Stack underflow: SUB requires at least two values.")
                b = stack.pop()
                a = stack.pop()
                stack.append(a - b)

            elif command == "MUL":
                if len(stack) < 2:
                    raise IndexError("Stack underflow: MUL requires at least two values.")
                b = stack.pop()
                a = stack.pop()
                stack.append(a * b)

            elif command == "DIV":
                if len(stack) < 2:
                    raise IndexError("Stack underflow: DIV requires at least two values.")
                b = stack.pop()
                a = stack.pop()
                if b == 0:
                    raise ZeroDivisionError("Runtime Error: Division by zero detected.")
                # Integer division (floor division)
                stack.append(a // b)

            elif command == "DUP":
                if not stack:
                    raise IndexError("Stack underflow: DUP requires at least one value.")
                stack.append(stack[-1])

            elif command == "SWAP":
                if len(stack) < 2:
                    raise IndexError("Stack underflow: SWAP requires at least two values.")
                b = stack.pop() # Top element
                a = stack.pop() # Second element
                stack.append(b)
                stack.append(a)

            # --- Comparison Operations (Pop b, Pop a -> Push 1/0) ---
            elif command == "EQ":
                if len(stack) < 2:
                    raise IndexError("Stack underflow: EQ requires at least two values.")
                b = stack.pop()
                a = stack.pop()
                stack.append(1 if a == b else 0)

            elif command == "GT":
                if len(stack) < 2:
                    raise IndexError("Stack underflow: GT requires at least two values.")
                b = stack.pop()
                a = stack.pop()
                stack.append(1 if a > b else 0)

            elif command == "LT":
                if len(stack) < 2:
                    raise IndexError("Stack underflow: LT requires at least two values.")
                b = stack.pop()
                a = stack.pop()
                stack.append(1 if a < b else 0)

            # --- Memory Operations ---
            elif command == "STORE":
                var_name = args[0]
                if not stack:
                    raise IndexError(f"Stack underflow: STORE requires a value for variable '{var_name}'.")
                value = stack.pop()
                memory[var_name] = value

            elif command == "LOAD":
                var_name = args[0]
                if var_name not in memory:
                    raise NameError(f"Variable '{var_name}' has not been stored yet.")
                stack.append(memory[var_name])


            # --- Output ---
            elif command == "PRINT":
                if not stack:
                    raise IndexError("Stack underflow: PRINT requires at least one value.")
                output.append(str(stack[-1]))

            # --- Control Flow Instructions (Jumps) ---
            elif command == "JMP":
                target_label = args[0]
                if target_label not in label_map:
                    raise NameError(f"Unknown label '{target_label}' for JMP.")
                program_counter = label_map[target_label]

            elif command == "JZ":
                target_label = args[0]
                if target_label not in label_map:
                    raise NameError(f"Unknown label '{target_label}' for JZ.")
                
                if len(stack) < 1:
                    raise IndexError("Stack underflow: JZ requires at least one value.")

                value = stack.pop()
                if value == 0:
                    program_counter = label_map[target_label]
                # else: fall through (PC increment handles this)

            elif command == "JNZ":
                target_label = args[0]
                if target_label not in label_map:
                    raise NameError(f"Unknown label '{target_label}' for JNZ.")
                
                if len(stack) < 1:
                    raise IndexError("Stack underflow: JNZ requires at least one value.")

                value = stack.pop()
                if value != 0:
                    program_counter = label_map[target_label]
                # else: fall through (PC increment handles this)

            # --- Subroutine Calls ---
            elif command == "CALL":
                target_label = args[0]
                if target_label not in label_map:
                    raise NameError(f"Unknown label '{target_label}' for CALL.")
                
                # Push return address (the instruction immediately following the CALL)
                call_stack.append(program_counter + 1)
                program_counter = label_map[target_label]

            elif command == "RET":
                if not call_stack:
                    raise RuntimeError("Runtime Error: RET executed with empty call stack.")
                
                # Pop the return address R. We set PC to R - 1 because the loop increments it.
                return_address = call_stack.pop()
                program_counter = return_address - 1

            # --- End of Instructions ---
            else:
                raise SyntaxError(f"Unknown command '{command}'")

        except (IndexError, ZeroDivisionError, ValueError, NameError, RuntimeError) as e:
            # Re-raise specific errors with context and stop execution
            raise type(e)(f"Line {line_num}: {e}")


        # Increment PC unless a jump/call/ret occurred (which already set the new PC)
        program_counter += 1

    return output
