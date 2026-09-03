def run(program: str) -> list[str]:
    lines = program.split('\n')
    stack = []
    output_lines = []

    def push(n):
        nonlocal stack
        stack.append(int(n))

    def pop():
        if not stack:
            raise ValueError(f"Stack underflow at line {line_number}")
        return stack.pop()

    def add():
        a = stack.pop()
        b = stack.pop()
        result = a + b
        stack.append(result)
        return f"{result}"

    def sub():
        a = stack.pop()
        b = stack.pop()
        if b == 0:
            raise ValueError(f"Division by zero at line {line_number}")
        result = a - b
        stack.append(result)
        return f"{result}"

    def mul():
        a = stack.pop()
        b = stack.pop()
        result = a * b
        stack.append(result)
        return f"{result}"

    def div():
        a = stack.pop()
        b = stack.pop()
        if b == 0:
            raise ValueError(f"Division by zero at line {line_number}")
        result = a // b
        stack.append(result)
        return f"{result}"

    def dup():
        val = stack[-1]
        stack.append(val)

    def swap():
        a = stack.pop()
        b = stack.pop()
        stack.append(a)
        stack.append(b)

    for line_num, line in enumerate(lines, start=1):
        if not line.strip() or line.startswith('#'):
            continue
        tokens = line.strip().split()
        cmd = tokens[0]
        args = tokens[1:] if len(tokens) > 1 else []

        try:
            if cmd == 'PUSH':
                push(args[0])
            elif cmd == 'POP':
                output_lines.append(pop())
            elif cmd == 'ADD':
                output_lines.append(add())
            elif cmd == 'SUB':
                output_lines.append(sub())
            elif cmd == 'MUL':
                output_lines.append(mul())
            elif cmd == 'DIV':
                output_lines.append(div())
            elif cmd == 'DUP':
                dup()
            elif cmd == 'SWAP':
                swap()
            elif cmd == 'PRINT':
                try:
                    val = stack[-1]
                    output_lines.append(val)
                except IndexError:
                    pass
        except ValueError as e:
            pass

    return output_lines
