"""
Simple stack-based interpreter for Python-like expressions.
Supported instructions:
  PUSH <n>      : push integer n
  POP           : pop top value
  ADD           : pop b, a; push a + b
  SUB           : pop b, a; push a - b
  MUL           : pop b, a; push a * b
  DIV           : pop b, a; floor(a / b)
  DUP           : duplicate top value
  SWAP          : swap top two values
  PRINT         : print top value without popping

Usage:
    python interpreter.py "PUSH 10\nPUSH 3\nADD"

Returns list of printed strings. Raises ValueError with line number for errors.
"""

import re
from typing import List, Tuple, Optional


class StackInterpreterError(ValueError):
    """Raised when an operation cannot be performed due to stack underflow or division by zero."""
    pass


def parse_input(lines: List[str]) -> Tuple[List[Tuple[int, int]], int]:
    """
    Parse input lines into (instruction, argument) pairs and ignore comments and empty lines.
    Returns a list of tuples where each tuple contains (instruction, argument_as_list).
    Instruction is always from the set {PUSH, POP, ADD, SUB, MUL, DIV, DUP, SWAP, PRINT}.
    """
    instructions: List[Tuple[str, list[int]]] = []

    # Remove comments first
    cleaned_lines = []
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        cleaned_lines.append(line)

    for line in cleaned_lines:
        parts = line.split()
        if len(parts) < 2:
            continue

        instr = parts[0]
        arg: List[int] = []
        i = 1
        while i < len(parts):
            token = parts[i]
            if token.isdigit():
                arg.append(int(token))
                i += 1
            else:
                raise ValueError(f"Expected an integer after '{parts[i]}' on line {line_num} (but found '{token}')")

        instructions.append((instr, arg))
    return instructions


def run(program: str) -> List[str]:
    """
    Run the program and return a list of printed strings.
    Raises StackInterpreterError if an operation cannot be performed.
    """
    # Pre-parse to collect valid instruction lines with their line numbers
    parsed: List[Tuple[int, int]] = []  # (instruction_name, args)

    stack: List[int] = []
    instructions: List[str] = []
    line_number: int = 1

    for line in program.splitlines():
        idx = line_number - 1
        stripped = line.strip()

        if not stripped or stripped.startswith("#"):
            # Skip empty lines and comments
            continue

        parts = stripped.split()
        if len(parts) < 2:
            raise ValueError(f"Malformed instruction on line {idx + 1}: expected at least one argument, got '{stripped}'")

        instr = parts[0]
        arg_list: List[int] = []
        i = 1
        while i < len(parts):
            token = parts[i]
            if token.isdigit():
                arg_list.append(int(token))
                i += 1
            else:
                raise ValueError(f"Invalid integer on line {idx + 1}")

        instructions.append((instr, arg_list))
        parsed.append((instr, arg_list))
        line_number = idx + 1

    if not instructions:
        return []

    while stack and len(parsed) > 0:
        _, args = parsed.pop()

        try:
            if instr == "PUSH":
                stack.extend(args)
            elif instr == "POP":
                if len(stack) < 1:
                    raise ValueError("POP attempted when stack is empty")
                val = stack.pop()
            elif instr == "ADD":
                if len(stack) < 2:
                    raise ValueError("ADD insufficient operands on line %d" % (line_number - 1))
                b, a = args
                if not isinstance(b, int) or not isinstance(a, int):
                    raise ValueError("ADD requires integers")
                stack.extend([a + b])
            elif instr == "SUB":
                if len(stack) < 2:
                    raise ValueError("SUB insufficient operands on line %d" % (line_number - 1))
                b, a = args
                if not isinstance(b, int) or not isinstance(a, int):
                    raise ValueError("SUB requires integers")
                stack.extend([a - b])
            elif instr == "MUL":
                if len(stack) < 2:
                    raise ValueError("MUL insufficient operands on line %d" % (line_number - 1))
                b, a = args
                if not isinstance(b, int) or not isinstance(a, int):
                    raise ValueError("MUL requires integers")
                stack.extend([a * b])
            elif instr == "DIV":
                if len(stack) < 2:
                    raise ValueError("DIV insufficient operands on line %d" % (line_number - 1))
                b, a = args
                if not isinstance(b, int) or not isinstance(a, int):
                    raise ValueError("DIV requires integers")
                stack.extend([a // b])
            elif instr == "DUP":
                if len(stack) < 1:
                    raise ValueError("DUP insufficient operands on line %d" % (line_number - 1))
                top = stack[-1]
                if not isinstance(top, int):
                    raise ValueError("DUP requires integer")
                stack.extend([top, top])
            elif instr == "SWAP":
                if len(stack) < 2:
                    raise ValueError("SWAP insufficient operands on line %d" % (line_number - 1))
                b, a = args
                # Stack is [..., a, b]; we need to pop both.
                # But the instruction says "pop two values". In stack-based designs like this,
                # usually POP returns the popped value as an argument and pops another value.
                # Here, since SWAP uses exactly two slots, it likely swaps the top two elements:
                # 1. Pop b (the second-to-top), then pop a (the top).
                # 2. Push b and a back in swapped order (or just swap positions).
                if len(stack) < 2:
                    raise ValueError("SWAP insufficient operands on line %d" % (line_number - 1))
                top = stack[-1]
                second = stack[-2]
                if not isinstance(top, int) or not isinstance(second, int):
                    raise ValueError("SWAP requires integers")
                # To swap: we pop both, then push them in the new order (second on top).
                stack.extend([second, top])  # effectively swapped
            elif instr == "PRINT":
                if len(stack) < 1:
                    raise ValueError("PRINT insufficient operands on line %d" % (line_number - 1))
                val = stack.pop()
            else:
                raise ValueError(f"Unknown instruction '{instr}' on line {line_number}")

        except StackInterpreterError as e:
            # Re-raise the original error with context
            raise from e
    return instructions
