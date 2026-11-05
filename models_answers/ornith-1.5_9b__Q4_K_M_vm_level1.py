class StackError(Exception):
    """Raised for invalid operations, with the offending line number."""


def run(program: str) -> list[str]:
    """Interpret a stack-based program and return the list of printed values."""
    stack = []
    output = []
    lines = program.splitlines()

    for idx, line in enumerate(lines):
        lineno = idx + 1
        stripped = line.strip()

        # Ignore empty lines and comments.
        if not stripped or stripped.startswith("#"):
            continue

        parts = stripped.split()
        op = parts[0].upper()

        try:
            if op == "PUSH":
                if len(parts) != 2:
                    raise StackError(f"Line {lineno}: PUSH requires exactly one argument")
                stack.append(int(parts[1]))

            elif op == "POP":
                if len(stack) < 1:
                    raise StackError(f"Line {lineno}: POP on empty stack")
                stack.pop()

            elif op == "ADD":
                if len(stack) < 2:
                    raise StackError(f"Line {lineno}: ADD needs two values")
                b = stack.pop()
                a = stack.pop()
                stack.append(a + b)

            elif op == "SUB":
                if len(stack) < 2:
                    raise StackError(f"Line {lineno}: SUB needs two values")
                b = stack.pop()
                a = stack.pop()
                stack.append(a - b)

            elif op == "MUL":
                if len(stack) < 2:
                    raise StackError(f"Line {lineno}: MUL needs two values")
                b = stack.pop()
                a = stack.pop()
                stack.append(a * b)

            elif op == "DIV":
                if len(stack) < 2:
                    raise StackError(f"Line {lineno}: DIV needs two values")
                b = stack.pop()
                a = stack.pop()
                if b == 0:
                    raise StackError(f"Line {lineno}: division by zero")
                stack.append(a // b)

            elif op == "DUP":
                if len(stack) < 1:
                    raise StackError(f"Line {lineno}: DUP on empty stack")
                stack.append(stack[-1])

            elif op == "SWAP":
                if len(stack) < 2:
                    raise StackError(f"Line {lineno}: SWAP needs two values")
                stack[-1], stack[-2] = stack[-2], stack[-1]

            elif op == "PRINT":
                if len(stack) < 1:
                    raise StackError(f"Line {lineno}: PRINT on empty stack")
                output.append(str(stack[-1]))

            else:
                raise StackError(f"Line {lineno}: unknown instruction '{op}'")

        except StackError:
            raise

    return output


if __name__ == "__main__":
    demo = """
        # A small demo program
        PUSH 10
        PUSH 20
        ADD          # 30
        DUP          # 30, 30
        SWAP         # 30, 30
        PRINT        # prints 30
        POP          # 30
        PUSH 100
        PUSH 6
        DIV          # 16
        PRINT        # prints 16
    """
    print(run(demo))
