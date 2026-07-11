#!/usr/bin/env python3
"""
Simple stack-based language interpreter.
"""

def _error(msg: str, line_no: int) -> None:
    raise RuntimeError(f"Line {line_no}: {msg}")

def run(program: str) -> list[str]:
    """
    Execute a program written in the simple stack language.

    Parameters
    ----------
    program : str
        Multi-line string containing the program.

    Returns
    -------
    list[str]
        List of strings printed by PRINT instructions.
    """
    stack = []
    output = []

    lines = program.splitlines()
    for idx, raw_line in enumerate(lines, start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        parts = line.split()
        instr = parts[0].upper()

        try:
            if instr == "PUSH":
                if len(parts) != 2:
                    _error("PUSH requires one argument", idx)
                stack.append(int(parts[1]))
            elif instr == "POP":
                if not stack:
                    _error("POP from empty stack", idx)
                stack.pop()
            elif instr == "ADD":
                if len(stack) < 2:
                    _error("ADD needs two operands", idx)
                b, a = stack.pop(), stack.pop()
                stack.append(a + b)
            elif instr == "SUB":
                if len(stack) < 2:
                    _error("SUB needs two operands", idx)
                b, a = stack.pop(), stack.pop()
                stack.append(a - b)
            elif instr == "MUL":
                if len(stack) < 2:
                    _error("MUL needs two operands", idx)
                b, a = stack.pop(), stack.pop()
                stack.append(a * b)
            elif instr == "DIV":
                if len(stack) < 2:
                    _error("DIV needs two operands", idx)
                b, a = stack.pop(), stack.pop()
                if b == 0:
                    _error("Division by zero", idx)
                stack.append(int(a / b))  # integer division
            elif instr == "DUP":
                if not stack:
                    _error("DUP from empty stack", idx)
                stack.append(stack[-1])
            elif instr == "SWAP":
                if len(stack) < 2:
                    _error("SWAP needs two operands", idx)
                stack[-1], stack[-2] = stack[-2], stack[-1]
            elif instr == "PRINT":
                if not stack:
                    _error("PRINT from empty stack", idx)
                output.append(str(stack[-1]))
            else:
                _error(f"Unknown instruction '{instr}'", idx)

        except ValueError as e:
            _error(f"Invalid number: {e}", idx)

    return output

if __name__ == "__main__":
    import sys
    prog = sys.stdin.read()
    try:
        for line in run(prog):
            print(line)
    except RuntimeError as err:
        sys.stderr.write(str(err) + "\n")
        sys.exit(1)
