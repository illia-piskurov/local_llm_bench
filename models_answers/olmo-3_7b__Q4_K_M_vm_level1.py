def run(program: str) -> list[str]:
    stack = []
    output = []
    lines = program.splitlines()
    for line_num, line in enumerate(lines, 1):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        parts = line.split()
        instruction = parts[0]
        if instruction == 'PUSH':
            n = int(parts[1])
            stack.append(n)
        elif instruction == 'POP':
            if not stack:
                raise Exception(f"Error on line {line_num}: POP on empty stack")
            stack.pop()
        elif instruction == 'ADD':
            if len(stack) < 2:
                raise Exception(f"Error on line {line_num}: not enough elements for ADD")
            a = stack.pop()
            b = stack.pop()
            stack.append(a + b)
        elif instruction == 'SUB':
            if len(stack) < 2:
                raise Exception(f"Error on line {line_num}: not enough elements for SUB")
            b = stack.pop()
            a = stack.pop()
            stack.append(a - b)
        elif instruction == 'MUL':
            if len(stack) < 2:
                raise Exception(f"Error on line {line_num}: not enough elements for MUL")
            a = stack.pop()
            b = stack.pop()
            stack.append(a * b)
        elif instruction == 'DIV':
            if len(stack) < 2:
                raise Exception(f"Error on line {line_num}: not enough elements for DIV")
            b = stack.pop()
            a = stack.pop()
            if b == 0:
                raise Exception(f"Error on line {line_num}: division by zero")
            stack.append(a // b)
        elif instruction == 'DUP':
            if not stack:
                raise Exception(f"Error on line {line_num}: DUP on empty stack")
            x = stack.pop()
            stack.append(x)
            stack.append(x)
        elif instruction == 'SWAP':
            if len(stack) < 2:
                raise Exception(f"Error on line {line_num}: not enough elements for SWAP")
            b = stack.pop()
            a = stack.pop()
            stack.append(b)
            stack.append(a)
        elif instruction == 'PRINT':
            if not stack:
                raise Exception(f"Error on line {line_num}: PRINT on empty stack")
            output.append(str(stack[-1]))
        else:
            raise Exception(f"Error on line {line_num}: unknown instruction '{instruction}'")
    return output
