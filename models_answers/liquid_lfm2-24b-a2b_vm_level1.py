def run(program: str) -> list[str]:
    stack = []
    output = []
    lines = [line for line in program.splitlines() if line.strip() and not line.startswith('#')]
    
    for idx, line in enumerate(lines, start=1):
        tokens = line.split()
        if not tokens:
            continue
        cmd = tokens[0].upper()
        
        if cmd == 'PUSH':
            if len(tokens) != 2:
                raise ValueError(f"PUSH requires one argument at line {idx}")
            try:
                n = int(tokens[1])
            except ValueError:
                raise ValueError(f"Invalid number at line {idx}")
            stack.append(n)
        
        elif cmd == 'POP':
            if not stack:
                raise IndexError(f"Stack underflow at line {idx}")
            output.append(str(stack.pop()))
        
        elif cmd == 'ADD':
            if len(stack) < 2:
                raise IndexError(f"Stack underflow during ADD at line {idx}")
            b = stack.pop()
            a = stack.pop()
            stack.append(a + b)
        
        elif cmd == 'SUB':
            if len(stack) < 2:
                raise IndexError(f"Stack underflow during SUB at line {idx}")
            b = stack.pop()
            a = stack.pop()
            stack.append(a - b)
        
        elif cmd == 'MUL':
            if len(stack) < 2:
                raise IndexError(f"Stack underflow during MUL at line {idx}")
            b = stack.pop()
            a = stack.pop()
            stack.append(a * b)
        
        elif cmd == 'DIV':
            if len(stack) < 2:
                raise IndexError(f"Stack underflow during DIV at line {idx}")
            b = stack.pop()
            a = stack.pop()
            if b == 0:
                raise ZeroDivisionError(f"Division by zero at line {idx}")
            stack.append(a // b)
        
        elif cmd == 'DUP':
            if not stack:
                raise IndexError(f"Stack underflow during DUP at line {idx}")
            stack.append(stack[-1])
        
        elif cmd == 'SWAP':
            if len(stack) < 2:
                raise IndexError(f"Stack underflow during SWAP at line {idx}")
            a = stack.pop()
            b = stack.pop()
            stack.extend([a, b])
        
        elif cmd == 'PRINT':
            if not stack:
                raise IndexError(f"Stack empty for PRINT at line {idx}")
            output.append(str(stack[-1]))
        
        else:
            raise ValueError(f"Unknown command {cmd} at line {idx}")
    
    return output
