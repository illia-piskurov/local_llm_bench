from typing import List

def run(program: str) -> List[str]:
    stack: List[int] = []
    lines = program.splitlines()
    labels: dict[str, int] = {}
    memory: dict[str, int] = {}
    call_stack: list[int] = []
    output: List[str] = []

    i = 0
    while i < len(lines):
        raw = lines[i].strip()
        if not raw or raw.startswith('#'):
            i += 1
            continue

        parts = raw.split()
        op = parts[0].upper()
        name = None
        arg = ''

        # LABEL definition
        if op == 'LABEL':
            name = parts[1]
            labels[name] = i
            i += 1
            continue

        # JMP, JZ, JNZ (conditional jump)
        elif op in ('JMP', 'JZ', 'JNZ'):
            if name not in labels:
                raise ValueError(f"Line {i}: Label '{name}' is undefined")
            target_line = labels[name]
            i = target_line
            continue

        # CALL / RET (subroutine call stack)
        elif op == 'CALL':
            name = parts[1]
            if name not in labels:
                raise ValueError(f"Line {i}: Label '{name}' is undefined")
            call_stack.append(i)          # push return address
            i = labels[name]               # jump to label, continue loop
            continue
        elif op == 'RET':
            if not call_stack:
                raise ValueError(f'Line {i}: No active CALL to unwind')
            return_line = call_stack.pop()
            i = return_line + 1           # resume after subroutine
            continue

        # PUSH / POP
        elif op == 'PUSH':
            stack.append(int(parts[1]))
            i += 1
        elif op == 'POP':
            if not stack:
                raise ValueError(f"Line {i}: Stack underflow (cannot POP)")
            stack.pop()
            i += 1

        # BINARY arithmetic: ADD, SUB, MUL, DIV
        else:
            if len(parts) < 3:
                raise ValueError(f"Line {i}: Not enough operands for '{op}'")
            b = stack.pop()
            a = stack.pop()

            try:
                if op == 'ADD':
                    result = a + b
                elif op == 'SUB':
                    result = a - b
                elif op == 'MUL':
                    result = a * b
                elif op == 'DIV':
                    if b == 0:
                        raise ZeroDivisionError(f"Line {i}: Division by zero")
                    result = a // b
            except Exception as exc:
                raise

            stack.append(result)
            i += 1

        # DUP / SWAP
        elif op == 'DUP':
            if not stack:
                raise ValueError(f"Line {i}: Stack underflow (cannot DUP)")
            stack.append(stack[-1])
            i += 1
        elif op == 'SWAP':
            if len(stack) < 2:
                raise ValueError(f"Line {i}: Not enough values to SWAP")
            a, b = stack.pop(), stack.pop()
            stack.append(a)
            stack.append(b)
            i += 1

        # PRINT
        elif op == 'PRINT':
            output.append(str(stack[-1]))
            i += 1

        # EQ / GT / LT (comparison operations)
        elif op in ('EQ', 'GT', 'LT'):
            b = stack.pop()
            a = stack.pop()
            if op == 'EQ':
                result = 1 if a == b else 0
            elif op == 'GT':
                result = 1 if a > b else 0
            elif op == 'LT':
                result = 1 if a < b else 0
            stack.append(result)
            i += 1

        # STORE / LOAD (named variables)
        elif op == 'STORE':
            var = parts[1]
            value = stack.pop()
            memory[var] = value
            i += 1
        elif op == 'LOAD':
            var = parts[1]
            if var not in memory:
                raise ValueError(f'Line {i}: LOAD from undefined variable '{var}'')
            stack.append(memory[var])
            i += 1

        else:
            raise ValueError(f"Line {i}: Unknown instruction '{op}'")

    return output
