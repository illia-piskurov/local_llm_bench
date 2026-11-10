from typing import List

def run(program: str) -> List[str]:
    stack: List[int] = []
    lines = program.splitlines()
    
    for line_no, raw in enumerate(lines, start=1):
        if not raw or raw.startswith('#'):
            continue
        
        parts = raw.split()
        op = parts[0].upper()
        
        try:
            if op == 'PUSH':
                stack.append(int(parts[1]))
            elif op == 'POP':
                if not stack:
                    raise ValueError(f"Line {line_no}: Stack underflow (cannot POP)")
                stack.pop()
            elif op == 'ADD':
                b = stack.pop(); a = stack.pop()
                stack.append(a + b)
            elif op == 'SUB':
                b = stack.pop(); a = stack.pop()
                stack.append(a - b)
            elif op == 'MUL':
                b = stack.pop(); a = stack.pop()
                stack.append(a * b)
            elif op == 'DIV':
                if not stack:
                    raise ValueError(f"Line {line_no}: Stack underflow (cannot DIV)")
                b = stack.pop()
                if b == 0:
                    raise ZeroDivisionError(f"Line {line_no}: Division by zero")
                a = stack.pop()
                stack.append(a // b)
            elif op == 'DUP':
                if not stack:
                    raise ValueError(f"Line {line_no}: Stack underflow (cannot DUP)")
                stack.append(stack[-1])
            elif op == 'SWAP':
                if len(stack) < 2:
                    raise ValueError(f"Line {line_no}: Not enough values to SWAP")
                a, b = stack.pop(), stack.pop()
                stack.append(a); stack.append(b)
            elif op == 'PRINT':
                stack.append(str(stack[-1]))
            else:
                raise ValueError(f"Line {line_no}: Unknown instruction '{op}'")
        except Exception as e:
            raise
    
    return stack

# Example usage (not part of required output):
# program = """PUSH 5\nPUSH 3\nPRINT\nADD\nPRINT"""
# print(run(program))  # Output: ['5', '8']
