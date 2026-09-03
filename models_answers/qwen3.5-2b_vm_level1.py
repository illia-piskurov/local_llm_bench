def run(program: str) -> list[str]:
    """Исполняет программу в стековом языке и возвращает список выведенных строк."""
    
    stack = []
    output_lines = []
    line_num = 0
    
    # Parse program into lines, handling comments and empty lines
    for i, line in enumerate(program.split('\n'), start=1):
        stripped_line = line.strip()
        
        if not stripped_line or stripped_line.startswith('#'):
            continue
        
        parts = stripped_line.split()
        if len(parts) == 0:
            continue
            
        instruction = parts[0]
        
        try:
            # Execute instructions based on type
            if instruction == 'PUSH':
                n_str = parts[1]
                stack.append(int(n_str))
            
            elif instruction == 'POP':
                if len(stack) > 0:
                    val = stack.pop()
                    # No output for POP
            
            elif instruction == 'ADD':
                b = stack.pop()
                a = stack.pop()
                stack.append(a + b)
            
            elif instruction == 'SUB':
                b = stack.pop()
                a = stack.pop()
                stack.append(a - b)
            
            elif instruction == 'MUL':
                b = stack.pop()
                a = stack.pop()
                stack.append(a * b)
            
            elif instruction == 'DIV':
                if len(stack) < 2:
                    raise ValueError(f"Stack underflow at line {i}")
                
                # Pop b then a (top is a, next is b) -> Wait.
                # "снимать два значения (b, затем a)" means pop b first? 
                # Usually stack top is 'a'. So we need to access bottom of the two popped values.
                # Let's assume standard LIFO: Top = a. Next = b.
                # Pop b -> stack has a at top.
                # Then pop a -> stack empty.
                
                if len(stack) < 2:
                    raise ValueError(f"Stack underflow at line {i}")
                
                val_b = stack.pop()
                val_a = stack.pop()
                stack.append(val_a // val_b) # Integer division
                
            elif instruction == 'DUP':
                if len(stack) > 0:
                    val = stack[-1]
                    stack.append(val * 2) # Wait, DUP usually duplicates value. 
                    # "продублировать значение на вершине стека" -> Push the top twice?
                    # Or push it again on top of existing? Yes, duplicate means push top onto stack.
                    # So if stack is [a, b], top is b. After DUP: [a, b, b].
                    # But wait, "продублировать" usually implies pushing the value onto the stack. 
                    # If I have a, b on stack. Top is b. Push b -> a, b, b.
                    
                else:
                    raise ValueError(f"Stack underflow at line {i}")
                
            elif instruction == 'SWAP':
                if len(stack) < 2:
                    raise ValueError(f"Stack underflow at line {i}")
                
                top = stack.pop() # Pop second value (top of two values)
                val_b = stack.pop() # Pop first value (bottom of two values)
                stack.append(val_b)
                stack.append(top)
            
            elif instruction == 'PRINT':
                if len(stack) > 0:
                    output_lines.append(str(stack[-1]))
                
        except ZeroDivisionError:
            raise ValueError(f"Divide by zero at line {i}")
        
    return output_lines
