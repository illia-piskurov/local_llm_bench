class StackUnderflowError(Exception):
    def __init__(self, line_number, instruction):
        self.line_number = line_number
        self.instruction = instruction
        message = (
            f"Stack underflow on line {line_number}: "
            f"{instruction} needs more values on the stack"
        )
        super().__init__(message)


class DivideByZeroError(Exception):
    def __init__(self, line_number, instruction):
        self.line_number = line_number
        self.instruction = instruction
        message = f"Division by zero on line {line_number}: {instruction}"
        super().__init__(message)


class LabelNotFoundError(Exception):
    def __init__(self, line_number, label):
        self.line_number = line_number
        self.label = label
        message = (
            f"Label '{label}' not defined on line {line_number}: "
            f"JMP/JZ/JNZ target"
        )
        super().__init__(message)


def run(program: str) -> list[str]:
    stack = []
    output = []
    labels = {}
    lines = program.splitlines()

    for line_number, raw_line in enumerate(lines, start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        parts = line.split()
        if not parts:
            continue

        instruction = parts[0]
        arguments = parts[1:]

        if instruction == "PUSH":
            if not arguments:
                raise StackUnderflowError(line_number, "PUSH")
            stack.append(int(arguments[0]))

        elif instruction == "POP":
            if not stack:
                raise StackUnderflowError(line_number, "POP")
            stack.pop()

        elif instruction == "ADD":
            if len(stack) < 2:
                raise StackUnderflowError(line_number, "ADD")
            b = stack.pop()
            a = stack.pop()
            stack.append(a + b)

        elif instruction == "SUB":
            if len(stack) < 2:
                raise StackUnderflowError(line_number, "SUB")
            b = stack.pop()
            a = stack.pop()
            stack.append(a - b)

        elif instruction == "MUL":
            if len(stack) < 2:
                raise StackUnderflowError(line_number, "MUL")
            b = stack.pop()
            a = stack.pop()
            stack.append(a * b)

        elif instruction == "DIV":
            if len(stack) < 2:
                raise StackUnderflowError(line_number, "DIV")
            b = stack.pop()
            a = stack.pop()
            if b == 0:
                raise DivideByZeroError(line_number, "DIV")
            stack.append(a // b)

        elif instruction == "DUP":
            if not stack:
                raise StackUnderflowError(line_number, "DUP")
            stack.append(stack[-1])

        elif instruction == "SWAP":
            if len(stack) < 2:
                raise StackUnderflowError(line_number, "SWAP")
            a, b = stack.pop(), stack.pop()
            stack.append(a)
            stack.append(b)

        elif instruction == "PRINT":
            if not stack:
                raise StackUnderflowError(line_number, "PRINT")
            output.append(str(stack[-1]))

        elif instruction == "LABEL":
            if not arguments:
                raise StackUnderflowError(line_number, "LABEL")
            labels[arguments[0]] = line_number

        elif instruction == "JMP":
            if not arguments:
                raise StackUnderflowError(line_number, "JMP")
            target = arguments[0]
            if target not in labels:
                raise LabelNotFoundError(line_number, target)
            line_number = labels[target]
            continue

        elif instruction == "JZ":
            if not arguments:
                raise StackUnderflowError(line_number, "JZ")
            target = arguments[0]
            if target not in labels:
                raise LabelNotFoundError(line_number, target)
            if not stack:
                raise StackUnderflowError(line_number, "JZ")
            value = stack.pop()
            if value == 0:
                line_number = labels[target]
                continue

        elif instruction == "JNZ":
            if not arguments:
                raise StackUnderflowError(line_number, "JNZ")
            target = arguments[0]
            if target not in labels:
                raise LabelNotFoundError(line_number, target)
            if not stack:
                raise StackUnderflowError(line_number, "JNZ")
            value = stack.pop()
            if value != 0:
                line_number = labels[target]
                continue

        else:
            raise ValueError(f"Unknown instruction on line {line_number}: {instruction}")

    return output
