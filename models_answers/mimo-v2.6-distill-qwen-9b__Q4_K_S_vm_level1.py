"""A simple stack-based language interpreter."""


class StackError(Exception):
    """Raised when an operation needs more values than are on the stack."""


def run(program: str) -> list[str]:
    """Interpret a program and return all strings printed by PRINT instructions."""
    output: list[str] = []

    for line_number, raw_line in enumerate(program.splitlines(), start=1):
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        parts = stripped.split()
        instruction = parts[0].upper()

        try:
            execute(instruction, parts[1:], line_number)
        except StackError as error:
            raise StackError(
                f"line {error.line}: not enough values on the stack for '{instruction}'"
            ) from None

    return output


def execute(instruction: str, arguments: list[str], line_number: int) -> None:
    """Execute one instruction using a shared interpreter stack."""
    if len(arguments) > 1 or instruction == "PRINT":
        raise ValueError(
            f"line {line_number}: unexpected extra argument(s) for '{instruction}'"
        )

    if instruction == "PUSH":
        try:
            value = int(arguments[0])
        except ValueError:
            raise ValueError(f"line {line_number}: invalid number '{arguments[0]}'") from None
        stack.push(value)
        return

    if instruction == "POP":
        stack.pop()
        return

    if instruction in ("ADD", "SUB", "MUL"):
        b, a = stack.pop(), stack.pop()
        if instruction == "ADD":
            stack.push(a + b)
        elif instruction == "SUB":
            stack.push(a - b)
        else:
            stack.push(a * b)
        return

    if instruction == "DIV":
        b, a = stack.pop(), stack.pop()
        if b == 0:
            raise ZeroDivisionError(f"line {line_number}: division by zero")
        stack.push(a // b)
        return

    if instruction == "DUP":
        value = stack.peek()
        stack.push(value)
        return

    if instruction == "SWAP":
        top, second = stack.pop(), stack.pop()
        stack.push(top)
        stack.push(second)
        return

    if instruction == "PRINT":
        output.append(str(stack.peek()))
        return

    raise ValueError(f"line {line_number}: unknown instruction '{instruction}'")


class Stack:
    """A simple list-backed value stack."""

    def __init__(self) -> None:
        self._values: list[int] = []

    @property
    def values(self) -> list[int]:
        return list(self._values)

    def push(self, value: int) -> None:
        self._values.append(value)

    def pop(self) -> int:
        if not self._values:
            raise StackError("the stack is empty")
        return self._values.pop()

    def peek(self) -> int:
        if not self._values:
            raise StackError("the stack is empty")
        return self._values[-1]


if __name__ == "__main__":
    program = """# Warm up the engine.
PUSH 5
PUSH 3
ADD
PRINT

# A little arithmetic.
PUSH 20
PUSH 4
DIV
SUB
MUL
DUP
SWAP
POP
PRINT"""
    for line in run(program):
        print(line)
