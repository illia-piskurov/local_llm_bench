def run(program: str) -> list[str]:
    """
    Executes the given program string.
    
    Arithmetic operations:
      ADD   = top2 + top1  (top2 is popped first)
      SUB   = top1 - top2
      MUL   = top1 * top2
      DIV   = top1 // top2   (integer division, raise if divisor == 0)
      DUP   = duplicate top element
      SWAP  = swap the two top elements

    PUSH n : push integer n onto stack.
    POP     : pop from stack; requires at least one element.
    PRINT  : output string of top element (without removing it).
    
    Returns:
        A list of strings: each call to PRINT appends a single line to this list.
    """
    stack = []          # holds integers
    outputs = []        # collected printed lines
    
    for line_no, raw_line in enumerate(program.splitlines(), start=1):
        line = raw_line.strip()
        
        # Skip empty lines and comments (lines starting with '#')
        if not line or line.lstrip().startswith('#'):
            continue
        
        parts = line.split()
        op = parts[0].upper()  # normalize to uppercase
        
        if op == 'PUSH':
            if len(parts) >= 2:
                try:
                    n = int(parts[1])
                except ValueError:
                    raise ValueError(f"line {line_no}: invalid number '{parts[1]}' for PUSH")
                stack.append(n)
            else:
                raise ValueError(f"line {line_no}: missing argument for PUSH (need a number)")
                
        elif op == 'POP':
            if not stack:
                raise RuntimeError(f"line {line_no}: POP requires at least one item on the stack")
            stack.pop()
                
        elif op == 'ADD':
            if len(stack) < 2:
                raise ValueError(f"line {line_no}: ADD needs two operands, got {len(stack)} items")
            b = stack.pop()   # top
            a = stack.pop()   # next
            stack.append(a + b)
                
        elif op == 'SUB':
            if len(stack) < 2:
                raise ValueError(f"line {line_no}: SUB needs two operands, got {len(stack)} items")
            b = stack.pop()
            a = stack.pop()
            stack.append(a - b)
                
        elif op == 'MUL':
            if len(stack) < 2:
                raise ValueError(f"line {line_no}: MUL needs two operands, got {len(stack)} items")
            a = stack.pop()
            b = stack.pop()
            stack.append(a * b)
                
        elif op == 'DIV':
            if len(stack) < 2:
                raise ValueError(f"line {line_no}: DIV needs two operands, got {len(stack)} items")
            b = stack.pop()
            a = stack.pop()
            if b == 0:
                raise ZeroDivisionError(f"line {line_no}: DIV by zero (divisor = {b})")
            stack.append(a // b)
                
        elif op == 'DUP':
            if not stack:
                raise ValueError(f"line {line_no}: DUP requires at least one item to duplicate")
            # push a copy of the top element
            stack.append(stack[-1])
                
        elif op == 'SWAP':
            if len(stack) < 2:
                raise ValueError(f"line {line_no}: SWAP needs two items, got only {len(stack)} on stack")
            b = stack.pop()   # top
            a = stack.pop()   # next
            stack.append(a)
            stack.append(b)   # put back in swapped order
            
        elif op == 'PRINT':
            if not stack:
                raise ValueError(f"line {line_no}: PRINT on empty stack")
            outputs.append(str(stack[-1]))
                
        else:
            raise ValueError(f"line {line_no}: unknown instruction '{op}'")
    
    return outputs
