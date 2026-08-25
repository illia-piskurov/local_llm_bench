#!/usr/bin/env python3
"""
Stack‑based language interpreter with labels, jumps, subroutines,
comparisons and named variables.
"""

def _error(msg: str, line_no: int) -> None:
    raise RuntimeError(f"Line {line_no}: {msg}")

def run(program: str) -> list[str]:
    """
    Execute a program written in the simple stack language.

    Parameters
    ----------
    program : str
        Multi‑line string containing the program.

    Returns
    -------
    list[str]
        List of strings printed by PRINT instructions.
    """
    # Preprocess lines and collect labels
    raw_lines = program.splitlines()
    lines: list[tuple[int, str]] = []
    label_map: dict[str, int] = {}
    for idx, raw_line in enumerate(raw_lines, start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        instr = parts[0].upper()
        if instr == "LABEL":
            if len(parts) != 2:
                _error("LABEL requires one argument", idx)
            name = parts[1]
            if name in label_map:
                _error(f"Duplicate label '{name}'", idx)
            label_map[name] = len(lines)
            # LABEL itself is not added to executable lines
        else:
            lines.append((idx, line))

    stack: list[int] = []
    call_stack: list[int] = []  # addresses of instructions after CALL
    memory: dict[str, int] = {}
    output: list[str] = []

    ip = 0  # instruction pointer

    while ip < len(lines):
        line_no, raw_line = lines[ip]
        parts = raw_line.split()
        instr = parts[0].upper()

        try:
            if instr == "PUSH":
                if len(parts) != 2:
                    _error("PUSH requires one argument", line_no)
                stack.append(int(parts[1]))
                ip += 1

            elif instr == "POP":
                if not stack:
                    _error("POP from empty stack", line_no)
                stack.pop()
                ip += 1

            elif instr in ("ADD", "SUB", "MUL", "DIV"):
                if len(stack) < 2:
                    _error(f"{instr} needs two operands", line_no)
                b, a = stack.pop(), stack.pop()
                if instr == "ADD":
                    stack.append(a + b)
                elif instr == "SUB":
                    stack.append(a - b)
                elif instr == "MUL":
                    stack.append(a * b)
                else:  # DIV
                    if b == 0:
                        _error("Division by zero", line_no)
                    stack.append(int(a / b))
                ip += 1

            elif instr == "DUP":
                if not stack:
                    _error("DUP from empty stack", line_no)
                stack.append(stack[-1])
                ip += 1

            elif instr == "SWAP":
                if len(stack) < 2:
                    _error("SWAP needs two operands", line_no)
                stack[-1], stack[-2] = stack[-2], stack[-1]
                ip += 1

            elif instr == "PRINT":
                if not stack:
                    _error("PRINT from empty stack", line_no)
                output.append(str(stack[-1]))
                ip += 1

            elif instr in ("JMP", "JZ", "JNZ"):
                if len(parts) != 2:
                    _error(f"{instr} requires one argument", line_no)
                target = parts[1]
                if target not in label_map:
                    _error(f"Undefined label '{target}'", line_no)
                if instr == "JMP":
                    ip = label_map[target]
                else:  # conditional
                    if not stack:
                        _error(f"{instr} from empty stack", line_no)
                    val = stack.pop()
                    cond = (val == 0) if instr == "JZ" else (val != 0)
                    ip = label_map[target] if cond else ip + 1

            elif instr in ("CALL"):
                if len(parts) != 2:
                    _error("CALL requires one argument", line_no)
                target = parts[1]
                if target not in label_map:
                    _error(f"Undefined label '{target}'", line_no)
                call_stack.append(ip + 1)  # address after CALL
                ip = label_map[target]

            elif instr == "RET":
                if not call_stack:
                    _error("RET with empty call stack", line_no)
                ip = call_stack.pop()

            elif instr in ("EQ", "GT", "LT"):
                if len(stack) < 2:
                    _error(f"{instr} needs two operands", line_no)
                b, a = stack.pop(), stack.pop()
                if instr == "EQ":
                    stack.append(1 if a == b else 0)
                elif instr == "GT":
                    stack.append(1 if a > b else 0)
                else:  # LT
                    stack.append(1 if a < b else 0)
                ip += 1

            elif instr == "STORE":
                if len(parts) != 2:
                    _error("STORE requires one argument", line_no)
                if not stack:
                    _error("STORE from empty stack", line_no)
                var = parts[1]
                memory[var] = stack.pop()
                ip += 1

            elif instr == "LOAD":
                if len(parts) != 2:
                    _error("LOAD requires one argument", line_no)
                var = parts[1]
                if var not in memory:
                    _error(f"Undefined variable '{var}'", line_no)
                stack.append(memory[var])
                ip += 1

            else:
                _error(f"Unknown instruction '{instr}'", line_no)

        except ValueError as e:
            _error(f"Invalid number: {e}", line_no)

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
