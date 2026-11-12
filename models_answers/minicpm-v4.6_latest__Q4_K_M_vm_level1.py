def run(program: str) -> list[str]:
    stack = []
    output = []
    line_number = 0
    for line in program.splitlines():
        # Skip comments and empty lines
        if line.strip() and line.strip().startswith('#'):
            continue
        if line.strip() == '':
            continue
        # Check if line is an instruction
        if line.startswith('PUSH'):
            n = int(line.split()[1])
            stack.append(n)
        elif line.startswith('POP'):
            if not stack:
                raise IndexError(f"Stack is empty before pop at line {line_number}")
            val = stack.pop()
        elif line.startswith('ADD'):
            a = stack.pop()
            b = stack.pop()
            stack.append(a + b)
        elif line.startswith('SUB'):
            b = stack.pop()
            a = stack.pop()
            stack.append(a - b)
        elif line.startswith('MUL'):
            b = stack.pop()
            a = stack.pop()
            stack.append(a * b)
        elif line.startswith('DIV'):
            b = stack.pop()
            a = stack.pop()
            if b == 0:
                raise ZeroDivisionError(f"Division by zero at line {line_number}")
            stack.append(a // b)
        elif line.startswith('DUP'):
            stack.append(stack.pop())
        elif line.startswith('SWAP'):
            if len(stack) >= 2:
                a = stack.pop()
                b = stack.pop()
                stack.append(b)
                stack.append(a)
        elif line.startswith('PRINT'):
            output.append(str(stack.pop()))
    return output

# Example usage: program = "PUSH 1 POP ADD POP DIV 2 DUP SWAP PRINT"
# This would return ["1", "2", "3", "6", "4", "5", ""]
