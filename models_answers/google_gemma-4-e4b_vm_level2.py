import re

def run(program: str) -> list[str]:
    """
    Runs the stack-based program and returns a list of printed strings.
    Raises an exception on runtime error (stack underflow, division by zero).
    Supports labels and conditional jumps.
    """
    stack = []
    output = []
    lines = [line.strip() for line in program.split('\n')]

    # --- Phase 1: Pre-process Labels ---
    label_map = {}
    for i, raw_line in enumerate(lines):
        line_num = i + 1
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
                # LABEL instructions are handled during parsing and do nothing here
                pass

            elif command == "PUSH":
                if args and args[0].isdigit():
                    stack.append(int(args[0]))
                else:
                    raise ValueError("PUSH requires a valid integer argument.")

            elif command == "POP":
                if not stack:
                    raise IndexError("Stack underflow: Cannot POP from an empty stack.")
                stack.pop()

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

            elif command == "PRINT":
                if not stack:
                    raise IndexError("Stack underflow: PRINT requires at least one value.")
                # Print the top value without popping it
                output.append(str(stack[-1]))

            # --- Control Flow Instructions ---
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
                else:
                    # If condition fails, fall through to the next instruction
                    pass

            elif command == "JNZ":
                target_label = args[0]
                if target_label not in label_map:
                    raise NameError(f"Unknown label '{target_label}' for JNZ.")
                
                if len(stack) < 1:
                    raise IndexError("Stack underflow: JNZ requires at least one value.")

                value = stack.pop()
                if value != 0:
                    program_counter = label_map[target_label]
                else:
                    # If condition fails, fall through to the next instruction
                    pass
            
            # --- End of Instructions ---
            else:
                raise SyntaxError(f"Unknown command '{command}'")

        except (IndexError, ZeroDivisionError, ValueError, NameError) as e:
            # Re-raise specific errors with context and stop execution
            raise type(e)(f"Line {line_num}: {e}")


        # Increment PC unless a jump occurred (which already set the new PC)
        program_counter += 1

    return output

if __name__ == '__main__':
    # Example 1: Basic arithmetic (Original Test)
    program1 = """
    PUSH 5
    PUSH 3
    ADD       # Stack: [8]
    DUP       # Stack: [8, 8]
    SUB       # Pop 8 (b), pop 8 (a). Push 0. Stack: [0]
    PRINT     # Output: 0
    PUSH 10
    POP       # Stack: []
    """
    print("--- Program 1 (Basic Arithmetic) ---")
    try:
        results = run(program1)
        print("Output:", results)
    except Exception as e:
        print("Error:", e)

    # Example 2: Division by zero and stack underflow (Original Test)
    program2 = """
    PUSH 10
    PUSH 0
    DIV       # Should fail here (Line 3)
    POP
    """
    print("\n--- Program 2 (Division by Zero) ---")
    try:
        run(program2)
    except Exception as e:
        print("Error:", e)

    # Example 3: Stack underflow on PRINT (Original Test)
    program3 = """
    PUSH 5
    POP       # Stack: []
    PRINT     # Should fail here (Line 3)
    """
    print("\n--- Program 3 (Stack Underflow) ---")
    try:
        run(program3)
    except Exception as e:
        print("Error:", e)

    # Example 4: SWAP and MUL (Original Test)
    program4 = """
    PUSH 2
    PUSH 3
    DUP       # Stack: [2, 3, 3]
    SWAP      # Pop 3 (b), pop 3 (a). Push b=3, a=2. Stack: [2, 3]
    MUL       # Pop 3 (b), pop 2 (a). Push 6. Stack: [6]
    PRINT     # Output: 6
    """
    print("\n--- Program 4 (SWAP/MUL) ---")
    try:
        results = run(program4)
        print("Output:", results)
    except Exception as e:
        print("Error:", e)

    # Example 5: JMP and Labels
    program5 = """
    PUSH 10
    LABEL start_calc
    PUSH 2
    PUSH 3
    ADD       # Stack: [15]
    JMP end_calc # Jump over the conditional logic
    
    PUSH 5
    POP
    
    LABEL check_zero
    PUSH 0
    DUP
    JZ skip_print # If top is 0, jump to skip_print
    PRINT       # This line should not run if JZ succeeds
    JMP end_calc

skip_print:
    PUSH 99
    POP
end_calc:
    PUSH 1
    DUP
"""
    print("\n--- Program 5 (Labels and JMP) ---")
    try:
        results = run(program5)
        # Expected output: [1] (from the final PUSH/DUP block)
        print("Output:", results)
    except Exception as e:
        print("Error:", e)

    # Example 6: JZ and JNZ flow control
    program6 = """
    PUSH 5
    LABEL check_value
    PUSH 0 # Value to test (0)
    DUP
    JNZ success_path # Since value is 0, this fails, falling through

    PRINT       # This runs because the jump failed (value == 0)
    JMP end_test

success_path:
    POP         # Should not run if JZ succeeds
    PUSH 99     # If we reach here, it means value != 0.
    
end_test:
    PRINT       # Final print
"""
    print("\n--- Program 6 (JZ/JNZ Flow Control - Test Case: Value=0) ---")
    try:
        results = run(program6)
        # Expected output: ["5"] (from the initial PUSH 5, then PRINT at line 12)
        print("Output:", results)
    except Exception as e:
        print("Error:", e)

    # Example 7: JZ/JNZ flow control - Test Case: Value=5
    program7 = """
    PUSH 5
    LABEL check_value
    PUSH 5 # Value to test (5)
    DUP
    JZ skip_path # Since value is 5, this fails, falling through

    PRINT       # This runs because the jump failed (value != 0)
    JMP end_test

skip_path:
    POP         # Should not run if JZ succeeds
    PUSH 99     # If we reach here, it means value == 0.
    
end_test:
    PRINT       # Final print
"""
    print("\n--- Program 7 (JZ/JNZ Flow Control - Test Case: Value=5) ---")
    try:
        results = run(program7)
        # Expected output: ["99"] (from the PUSH 99 block, which is skipped by JZ failure)
        print("Output:", results)
    except Exception as e:
        print("Error:", e)
