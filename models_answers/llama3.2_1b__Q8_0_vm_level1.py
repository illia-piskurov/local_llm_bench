def run(program):
    stack = []
    for line in program.split('\n'):
        if line.strip().startswith('#'):
            continue
        op, *args = line.split()
        if op == 'PUSH':
            try:
                stack.append(int(args[0]))
            except ValueError:
                raise ValueError(f"Invalid PUSH instruction: {line}")
        elif op == 'POP':
            if not stack:
                raise ValueError(f"Stack is empty: {line}")
            stack.pop()
        elif op == 'ADD':
            if len(stack) < 2:
                raise ValueError(f"Stack does not have enough values for ADD: {line}")
            a = stack.pop()
            b = stack.pop()
            stack.append(a + b)
        elif op == 'SUB':
            if len(stack) < 2:
                raise ValueError(f"Stack does not have enough values for SUB: {line}")
            a = stack.pop()
            b = stack.pop()
            if b == 0:
                raise ZeroDivisionError(f"Division by zero: {line}")
            stack.append(a - b)
        elif op == 'MUL':
            if len(stack) < 2:
                raise ValueError(f"Stack does not have enough values for MUL: {line}")
            a = stack.pop()
            b = stack.pop()
            stack.append(a * b)
        elif op == 'DIV':
            if len(stack) < 2:
                raise ValueError(f"Stack does not have enough values for DIV: {line}")
            a = stack.pop()
            b = stack.pop()
            if b == 0:
                raise ZeroDivisionError(f"Division by zero: {line}")
            stack.append(a // b)
        elif op == 'DUP':
            if len(stack) < 1:
                raise ValueError(f"Stack is empty: {line}")
            stack.append(stack[-1])
        elif op == 'SWAP':
            if len(stack) < 2:
                raise ValueError(f"Stack does not have enough values for SWAP: {line}")
            a, b = stack.pop(), stack.pop()
            stack.append(a)
            stack.append(b)
        elif op == 'PRINT':
            if not stack:
                raise ValueError(f"Stack is empty: {line}")
            print(stack[-1])
    return stack
