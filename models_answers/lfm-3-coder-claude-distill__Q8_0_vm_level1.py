import re


def run(program: str) -> list[str]:
    """Interpreter for a simple stack-based language.
    
    Args:
        program: multi-line source code (comments and empty lines are ignored)
        
    Returns:
        List of strings representing PRINT outputs from the execution.
    """
    stack = []
    outputs = []

    lines = program.splitlines()

    for line_num, raw_line in enumerate(lines, start=1):
        stripped = raw_line.strip()

        # Skip empty lines and comments
        if not stripped or stripped.startswith('#'):
            continue

        parts = stripped.split()
        if len(parts) < 1:
            continue

        op = parts[0].upper()

        try:
            if op == 'PUSH':
                if len(parts) < 2:
                    raise ValueError(f"Line {line_num}: PUSH requires an argument, got '{stripped}'")
                value_str = parts[1]
                try:
                    value = int(value_str)
                except ValueError:
                    raise ValueError(
                        f"Line {line_num}: PUSH expects a number, got '{value_str}'"
                    )
                stack.append(value)

            elif op == 'POP':
                if len(stack) < 1:
                    raise IndexError(f"Line {line_num}: POP requires at least one value on the stack")
                stack.pop()

            elif op in ('ADD', 'SUB', 'MUL', 'DIV'):
                if len(stack) < 2:
                    raise ValueError(
                        f"Line {line_num}: '{op}' requires two values, got {len(stack)}"
                    )

                b = stack.pop()
                a = stack.pop()

                if op == 'ADD':
                    result = a + b
                elif op == 'SUB':
                    result = a - b
                elif op == 'MUL':
                    result = a * b
                elif op == 'DIV':
                    if b == 0:
                        raise ZeroDivisionError(
                            f"Line {line_num}: DIV by zero (b={b})"
                        )
                    result = a // b

                stack.append(result)

            elif op == 'DUP':
                if len(stack) < 1:
                    raise IndexError(f"Line {line_num}: DUP requires at least one value on the stack")
                stack.append(stack[-1])

            elif op == 'SWAP':
                if len(stack) < 2:
                    raise ValueError(
                        f"Line {line_num}: SWAP requires two values, got {len(stack)}"
                    )
                b = stack.pop()
                a = stack.pop()
                stack.append(a)
                stack.append(b)

            else:
                raise ValueError(f"Unknown instruction '{op}' on line {line_num}")

        except IndexError as e:
            # Wrap underflow errors into our own clear, line-numbered error
            raise RuntimeError(
                f"Line {e.args[0].split(':')[0] + 1}: "
                f"Stack underflow — not enough values for operation '{op}'"
            ) from e

    return outputs
