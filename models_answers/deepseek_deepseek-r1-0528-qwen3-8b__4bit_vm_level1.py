def run(program: str) -> list[str]:
    lines = program.splitlines()
    outputs = []
    stack = []
    
    def error(message: str, line_num: int):
        raise ValueError(f"Error on line {line_num}: {message}")
    
    current_line = 1
    for line in lines:
        stripped_line = line.lstrip()
        if not stripped_line or stripped_line.startswith('#'):
            current_line += 1
            continue
            
        parts = stripped_line.split()
        command = parts[0].upper() if len(parts) > 0 else ''
        
        try:
            current_line += 1
            if command == 'PUSH':
                if len(parts) != 2:
                    error("Invalid number of arguments", current_line - 1)
                try:
                    n = int(parts[1])
                    stack.append(n)
                    current_line += 1
                except ValueError:
                    error("PUSH requires an integer", current_line - 1)
                    
            elif command == 'POP':
                if stack:
                    popped = stack.pop()
                    # No output handled here, outputs are collected separately
                else:
                    error("Cannot POP from empty stack", current_line - 1)
                    
            elif command == 'ADD':
                if len(stack) < 2:
                    error("Need at least two elements to add", current_line - 1)
                try:
                    a = stack.pop()
                    b = stack.pop()
                    # Pushes in the order of first popped being a, second being b
                    stack.append(b + a)
                except (TypeError, ValueError):
                    error("Both operands must be integers", current_line - 1)
                    
            elif command == 'SUB':
                if len(stack) < 2:
                    error("Need at least two elements to subtract", current_line - 1)
                try:
                    a = stack.pop()
                    b = stack.pop()
                    stack.append(b - a)
                except (TypeError, ValueError):
                    error("Both operands must be integers", current_line - 1)
                    
            elif command == 'MUL':
                if len(stack) < 2:
                    error("Need at least two elements to multiply", current_line - 1)
                try:
                    a = stack.pop()
                    b = stack.pop()
                    stack.append(b * a)
                except (TypeError, ValueError):
                    error("Both operands must be integers", current_line - 1)
                    
            elif command == 'DIV':
                if len(stack) < 2:
                    error("Need at least two elements to divide", current_line - 1)
                try:
                    a = stack.pop()
                    b = stack.pop()
                    if not isinstance(b, int) or not isinstance(a, int):
                        error("Both operands must be integers", current_line - 1)
                    if b == 0:
                        error("Division by zero", current_line - 1)
                    stack.append(b // a)
                except (TypeError, ValueError):
                    error("Both operands must be integers", current_line - 1)
                    
            elif command == 'DUP':
                if not stack:
                    error("Cannot DUP in empty stack", current_line - 1)
                value = stack.pop()
                # Push back the popped value without popping it first
                if isinstance(value, int):
                    stack.append(value)
                else:
                    error("DUP requires an integer", current_line - 1)
                    
            elif command == 'SWAP':
                if len(stack) < 2:
                    error("Need at least two elements to swap", current_line - 1)
                try:
                    a = stack.pop()
                    b = stack.pop()
                    # Swap them before pushing back
                    stack.append(b)
                    stack.append(a)
                except (TypeError, ValueError):
                    error("SWAP requires two elements", current_line - 1)
                    
            elif command == 'PRINT':
                if not stack:
                    error("Cannot print from empty stack", current_line - 1)
                # If the top element is an integer, print it; otherwise raise error
                value = stack.pop()
                if isinstance(value, int):
                    result = str(value)
                    # Push back the popped value to maintain stack state
                    if line.startswith('PUSH ') or len(line) > 5:
                        # If the instruction was a PUSH with valid integer, re-push it
                        try:
                            stack.append(int(parts[1]))
                        except IndexError:
                            pass  # Otherwise, leave the value as popped but not integer
                    outputs.append(result)
                else:
                    error("Cannot print non-integer", current_line - 1)

        except (ValueError, TypeError) as e:
            # These are already raised appropriately above
            pass

    return outputs
