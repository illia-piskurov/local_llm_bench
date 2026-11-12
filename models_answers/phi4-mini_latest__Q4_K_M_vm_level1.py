def run(program: str) -> list[str]:
    instructions = program.strip().split('\n')
    stack = []
    output = []
    for i, instruction in enumerate(instructions, 1):
        if not instruction.strip() or instruction.startswith('#'):
            continue
        parts = instruction.split()
        command = parts[0]
        if command == 'PUSH':
            stack.append(int(parts[1]))
        elif command == 'POP':
            if not stack:
                raise Exception(f"Error on line {i}: stack underflow")
            stack.pop()
        elif command == 'ADD':
            if len(stack) < 2:
                raise Exception(f"Error on line {i}: stack underflow")
            a, b = stack.pop(), stack.pop()
            stack.append(a + b)
        elif command == 'SUB':
            if len(stack) < 2:
                raise Exception(f"Error on line {i}: stack underflow")
            a, b = stack.pop(), stack.pop()
            stack.append(a - b)
        elif command == 'MUL':
            if len(stack) < 2:
                raise Exception(f"Error on line {i}: stack underflow")
            a, b = stack.pop(), stack.pop()
            stack.append(a * b)
        elif command == 'DIV':
            if len(stack) < 2:
                raise Exception(f"Error on line {i}: stack underflow")
            a, b = stack.pop(), stack.pop()
            if b == 0:
                raise Exception(f"Error on line {i}: division by zero")
            stack.append(a // b)
        elif command == 'DUP':
            if not stack:
                raise Exception(f"Error on line {i}: stack underflow")
            stack.append(stack[-1])
        elif command == 'SWAP':
            if len(stack) < 2:
                raise Exception(f"Error on line {i}: stack underflow")
            stack[-1], stack[-2] = stack[-2], stack[-1]
        elif command == 'PRINT':
            if not stack:
                raise Exception(f"Error on line {i}: stack underflow")
            output.append(str(stack[-1]))
        else:
            raise Exception(f"Unknown command on line {i}: {command}")
    return output

# Example usage:
# program = """
# PUSH 3
# PUSH 4
# ADD
# PRINT
# """
# print(run(program))
