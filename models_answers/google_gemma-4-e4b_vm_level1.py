import re

def run(program: str) -> list[str]:
    """
    Runs the stack-based program and returns a list of printed strings.
    Raises an exception on runtime error (stack underflow, division by zero).
    """
    stack = []
    output = []
    lines = program.strip().split('\n')

    # Helper function to process instructions safely
    def execute_instruction(line: str, line_num: int):
        parts = line.split()
        if not parts:
            return # Should not happen if filtering is correct

        command = parts[0]
        args = parts[1:]

        try:
            if command == "PUSH":
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

        except (IndexError, ZeroDivisionError, ValueError) as e:
            # Re-raise specific errors with context
            raise type(e)(f"Line {line_num}: {e}")


    for i, raw_line in enumerate(lines):
        line_num = i + 1
        line = raw_line.strip()

        # Ignore empty lines and comments
        if not line or line.startswith("#"):
            continue

        try:
            execute_instruction(line, line_num)
        except Exception as e:
            # If any error occurs during execution, stop and raise the formatted error
            raise e

    return output

if __name__ == '__main__':
    # Example 1: Basic arithmetic
    program1 = """
    PUSH 5
    PUSH 3
    ADD       # Stack: [8]
    DUP       # Stack: [8, 8]
    SUB       # Pop 8 (b), pop 8 (a). Push 8 - 8 = 0. Stack: [0]
    PRINT     # Output: 0
    PUSH 10
    POP       # Stack: []
    """
    print("--- Program 1 ---")
    try:
        results = run(program1)
        print("Output:", results)
    except Exception as e:
        print("Error:", e)

    # Example 2: Division by zero and stack underflow
    program2 = """
    PUSH 10
    PUSH 0
    DIV       # Should fail here (Line 3)
    POP
    """
    print("\n--- Program 2 ---")
    try:
        run(program2)
    except Exception as e:
        print("Error:", e)

    # Example 3: Stack underflow on PRINT
    program3 = """
    PUSH 5
    POP       # Stack: []
    PRINT     # Should fail here (Line 3)
    """
    print("\n--- Program 3 ---")
    try:
        run(program3)
    except Exception as e:
        print("Error:", e)

    # Example 4: SWAP and MUL
    program4 = """
    PUSH 2
    PUSH 3
    DUP       # Stack: [2, 3, 3]
    SWAP      # Pop 3 (b), pop 3 (a). Push 3, then 2. Stack: [2, 3] -> Wait, SWAP pops two and pushes them back in order b, a.
               # Initial stack: [2, 3]. DUP makes it [2, 3, 3].
               # SWAP pops 3 (b), pop 3 (a). Pushes b=3, then a=2. Stack: [2, 3]
    MUL       # Pop 3 (b), pop 2 (a). Push 6. Stack: [6]
    PRINT     # Output: 6
    """
    print("\n--- Program 4 ---")
    try:
        results = run(program4)
        print("Output:", results)
    except Exception as e:
        print("Error:", e)
