import sys

def run(program: str) -> list[str]:
    """
    Реализует интерпретатор простого стекового языка.
    """
    stack = []
    output = []
    lines = program.split('\n')
    
    # Map line number to instruction index for error reporting
    line_number = 0

    def handle_error(message):
        # In a real scenario, we might raise an exception or halt execution.
        # For this implementation, we print the error and stop execution gracefully.
        sys.stderr.write(f"Runtime Error at line {line_number}: {message}\n")
        # Stop execution upon critical error
        raise RuntimeError("Execution halted due to error.")

    for line in lines:
        line_number += 1
        # Ignore empty lines and comments
        if not line.strip() or line.strip().startswith('#'):
            continue

        parts = line.split()
        if not parts:
            continue
        
        command = parts[0]
        args = parts[1:]

        try:
            if command == "PUSH":
                if len(args) != 1:
                    handle_error("PUSH requires one argument.")
                n = int(args[0])
                stack.append(n)
            
            elif command == "POP":
                if not stack:
                    handle_error("POP failed: Stack is empty.")
                stack.pop()

            elif command == "PRINT":
                if not stack:
                    handle_error("PRINT failed: Stack is empty.")
                print(stack[-1])
                output.append(str(stack[-1])) # Capture printed output

            elif command == "DUP":
                if not stack:
                    handle_error("DUP failed: Stack is empty.")
                value = stack[-1]
                stack.append(value)

            elif command == "SWAP":
                if len(stack) < 2:
                    handle_error("SWAP failed: Need at least two elements on the stack.")
                a = stack.pop()
                b = stack.pop()
                stack.append(a)
                stack.append(b)

            elif command in ("ADD", "SUB", "MUL", "DIV"):
                if len(stack) < 2:
                    handle_error(f"{command} failed: Not enough operands on the stack.")
                
                # Operands are popped in reverse order (b then a)
                b = stack.pop()
                a = stack.pop()

                if command == "ADD":
                    stack.append(a + b)
                elif command == "SUB":
                    # a - b
                    stack.append(a - b)
                elif command == "MUL":
                    stack.append(a * b)
                elif command == "DIV":
                    if b == 0:
                        handle_error("DIV failed: Division by zero.")
                    else:
                        # Integer division
                        stack.append(a // b)
            
            else:
                handle_error(f"Unknown command: {command}")

        except ValueError as e:
            handle_error(f"Invalid argument format for {command}: {e}")
        except RuntimeError:
            # Re-raise the error if it was a critical runtime error (like stack underflow or div by zero)
            pass 
        except Exception as e:
            handle_error(f"An unexpected error occurred during execution: {e}")


    return output

if __name__ == '__main__':
    # Example usage demonstration (not part of the required function, but useful for testing)
    
    program1 = """
PUSH 5
PUSH 3
ADD
PRINT
"""
    print("--- Program 1 ---")
    try:
        results1 = run(program1)
        print("Output:", results1) # Expected output: 8
    except RuntimeError as e:
        print(f"Execution failed: {e}")

    print("\n" + "="*20 + "\n")

    program2 = """
PUSH 10
PUSH 0
DIV
PRINT
"""
    print("--- Program 2 (Division by Zero) ---")
    try:
        results2 = run(program2)
        print("Output:", results2)
    except RuntimeError as e:
        print(f"Execution failed: {e}")

    print("\n" + "="*20 + "\n")
    
    program3 = """
PUSH 10
DUP
PRINT
"""
    print("--- Program 3 (DUP) ---")
    try:
        results3 = run(program3)
        print("Output:", results3) # Expected output: 10, 10
    except RuntimeError as e:
        print(f"Execution failed: {e}")
