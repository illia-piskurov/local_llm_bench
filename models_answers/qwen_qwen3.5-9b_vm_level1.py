def run(program: str) -> list[str]:
    stack = []
    output = []
    lines = program.splitlines()
    
    for i, line in enumerate(lines):
        line_num = i + 1
        stripped = line.strip()
        
        # Skip empty lines and comments
        if not stripped or stripped.startswith('#'):
            continue
        
        parts = stripped.split()
        instruction = parts[0].upper()
        
        try:
            if instruction == 'PUSH':
                if len(parts) < 2:
                    raise RuntimeError(f"Line {line_num}: PUSH requires an argument")
                stack.append(int(parts[1]))
            
            elif instruction == 'POP':
                if not stack:
                    raise RuntimeError(f"Line {line_num}: Stack underflow on POP")
                stack.pop()
                
            elif instruction == 'ADD':
                if len(stack) < 2:
                    raise RuntimeError(f"Line {line_num}: Stack underflow on ADD")
                b = stack.pop()
                a = stack.pop()
                stack.append(a + b)
                
            elif instruction == 'SUB':
                if len(stack) < 2:
                    raise RuntimeError(f"Line {line_num}: Stack underflow on SUB")
                b = stack.pop()
                a = stack.pop()
                stack.append(a - b)
                
            elif instruction == 'MUL':
                if len(stack) < 2:
                    raise RuntimeError(f"Line {line_num}: Stack underflow on MUL")
                b = stack.pop()
                a = stack.pop()
                stack.append(a * b)
                
            elif instruction == 'DIV':
                if len(stack) < 2:
                    raise RuntimeError(f"Line {line_num}: Stack underflow on DIV")
                b = stack.pop()
                a = stack.pop()
                if b == 0:
                    raise RuntimeError(f"Line {line_num}: Division by zero")
                stack.append(a // b)
                
            elif instruction == 'DUP':
                if not stack:
                    raise RuntimeError(f"Line {line_num}: Stack underflow on DUP")
                stack.append(stack[-1])
                
            elif instruction == 'SWAP':
                if len(stack) < 2:
                    raise RuntimeError(f"Line {line_num}: Stack underflow on SWAP")
                a = stack.pop()
                b = stack.pop()
                stack.append(a)
                stack.append(b)
                
            elif instruction == 'PRINT':
                if not stack:
                    raise RuntimeError(f"Line {line_num}: Stack underflow on PRINT")
                output.append(str(stack[-1]))
            
            else:
                raise RuntimeError(f"Line {line_num}: Unknown instruction '{instruction}'")
                
        except ValueError:
            raise RuntimeError(f"Line {line_num}: Invalid integer argument") from None
            
    return output
