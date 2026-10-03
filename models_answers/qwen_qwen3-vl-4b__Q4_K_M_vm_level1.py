def run(program: str) -> list[str]:
    lines = program.splitlines()
    stack = []
    output = []
    current_line = 0
    
    for line in lines:
        # Skip empty lines and comments
        if not line.strip() or line.strip().startswith("#"):
            continue
        
        parts = line.split()
        instruction = parts[0]
        
        if instruction == "PUSH":
            try:
                n = int(parts[1])
                stack.append(n)
            except ValueError:
                raise ValueError(f"Line {current_line + 1}: Invalid number for PUSH")
                
        elif instruction == "POP":
            if len(stack) == 0:
                raise ValueError(f"Line {current_line + 1}: Stack is empty, cannot POP")
            stack.pop()
            
        elif instruction == "ADD":
            if len(stack) < 2:
                raise ValueError(f"Line {current_line + 1}: Stack has less than 2 elements for ADD")
            b = stack.pop()
            a = stack.pop()
            stack.append(a + b)
            
        elif instruction == "SUB":
            if len(stack) < 2:
                raise ValueError(f"Line {current_line + 1}: Stack has less than 2 elements for SUB")
            b = stack.pop()
            a = stack.pop()
            stack.append(a - b)
            
        elif instruction == "MUL":
            if len(stack) < 2:
                raise ValueError(f"Line {current_line + 1}: Stack has less than 2 elements for MUL")
            b = stack.pop()
            a = stack.pop()
            stack.append(a * b)
            
        elif instruction == "DIV":
            if len(stack) < 2:
                raise ValueError(f"Line {current_line + 1}: Stack has less than 2 elements for DIV")
            b = stack.pop()
            a = stack.pop()
            if b == 0:
                raise ValueError(f"Line {current_line + 1}: Division by zero")
            stack.append(a // b)
            
        elif instruction == "DUP":
            if len(stack) == 0:
                raise ValueError(f"Line {current_line + 1}: Stack is empty, cannot DUP")
            stack.append(stack[-1])
            
        elif instruction == "SWAP":
            if len(stack) < 2:
                raise ValueError(f"Line {current_line + 1}: Stack has less than 2 elements for SWAP")
            stack[-1], stack[-2] = stack[-2], stack[-1]
            
        elif instruction == "PRINT":
            if len(stack) == 0:
                raise ValueError(f"Line {current_line + 1}: Stack is empty, cannot PRINT")
            output.append(str(stack[-1]))
            # Do not pop the value
        else:
            raise ValueError(f"Line {current_line + 1}: Unknown instruction: {instruction}")
        
        current_line += 1
    
    return output
