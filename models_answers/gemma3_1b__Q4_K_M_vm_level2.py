def run(program: str) -> list[str]:
    """
    Runs the given program.
    """
    try:
        stack = []
        for line in program.splitlines():
            line = line.strip()
            if line.startswith("PUSH"):
                args = line[3:].split()
                if len(args) != 2:
                    raise ValueError("Invalid PUSH format")
                n = int(args[0])
                stack.append(n)
            elif line.startswith("POP"):
                if len(stack) == 0:
                    raise ValueError("Stack is empty")
                popped = stack.pop()
                print(popped)
            elif line.startswith("ADD"):
                if len(stack) != 2:
                    raise ValueError("Invalid ADD format")
                b, a = stack.pop(), stack.pop()
                stack.append(a + b)
            elif line.startswith("SUB"):
                if len(stack) != 2:
                    raise ValueError("Invalid SUB format")
                b, a = stack.pop(), stack.pop()
                stack.append(a - b)
            elif line.startswith("MUL"):
                if len(stack) != 2:
                    raise ValueError("Invalid MUL format")
                b, a = stack.pop(), stack.pop()
                stack.append(a * b)
            elif line.startswith("DIV"):
                if len(stack) != 2:
                    raise ValueError("Invalid DIV format")
                b, a = stack.pop(), stack.pop()
                if b == 0:
                    raise ZeroDivisionError("Division by zero")
                stack.append(a // b)
            elif line.startswith("DUP"):
                if len(stack) != 0:
                    raise ValueError("Invalid DUP format")
                stack.append(stack[-1])
            elif line.startswith("SWAP"):
                if len(stack) != 0:
                    raise ValueError("Invalid SWAP format")
                stack[-1], stack[-2] = stack[-2], stack[-1]
            elif line.startswith("PRINT"):
                if len(stack) != 0:
                    raise ValueError("Invalid PRINT format")
                    print(stack.pop())
            else:
                raise ValueError(line)
    except ValueError as e:
        print(f"Error: {e}")
    except ZeroDivisionError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    return list(stack)
