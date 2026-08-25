def run(program: str) -> list[str]:
    stack = []
    output = []
    lines = program.splitlines()

    for line_idx, raw_line in enumerate(lines, 1):
        line = raw_line.strip()
        
        # Игнорируем пустые строки и комментарии
        if not line or line.startswith('#'):
            continue
        
        parts = line.split()
        command = parts[0].upper()
        args = parts[1:]

        try:
            if command == "PUSH":
                if not args:
                    raise ValueError("PUSH requires an argument")
                stack.append(int(args[0]))

            elif command == "POP":
                if len(stack) < 1:
                    raise IndexError("Stack underflow: cannot POP from empty stack")
                stack.pop()

            elif command == "ADD":
                if len(stack) < 2:
                    raise IndexError("Stack underflow: ADD requires 2 values")
                b = stack.pop()
                a = stack.pop()
                stack.append(a + b)

            elif command == "SUB":
                if len(stack) < 2:
                    raise IndexError("Stack underflow: SUB requires 2 values")
                b = stack.pop()
                a = stack.pop()
                stack.append(a - b)

            elif command == "MUL":
                if len(stack) < 2:
                    raise IndexError("Stack underflow: MUL requires 2 values")
                b = stack.pop()
                a = stack.pop()
                stack.append(a * b)

            elif command == "DIV":
                if len(stack) < 2:
                    raise IndexError("Stack underflow: DIV requires 2 values")
                b = stack.pop()
                a = stack.pop()
                if b == 0:
                    raise ZeroDivisionError("Division by zero")
                stack.append(a // b)

            elif command == "DUP":
                if len(stack) < 1:
                    raise IndexError("Stack underflow: DUP requires 1 value")
                stack.append(stack[-1])

            elif command == "SWAP":
                if len(stack) < 2:
                    raise IndexError("Stack underflow: SWAP requires 2 values")
                stack[-1], stack[-2] = stack[-2], stack[-1]

            elif command == "PRINT":
                if len(stack) < 1:
                    raise IndexError("Stack underflow: PRINT requires 1 value")
                output.append(str(stack[-1]))

            else:
                raise ValueError(f"Unknown command: {command}")

        except (IndexError, ZeroDivisionError, ValueError) as e:
            # Перехватываем ошибки стека, деления и парсинга аргументов
            # и выбрасываем их с указанием строки
            error_msg = str(e)
            if "Stack underflow" in error_msg:
                raise RuntimeError(f"Error at line {line_idx}: {error_msg}")
            elif "Division by zero" in error_msg:
                raise RuntimeError(f"Error at line {line_idx}: Division by zero")
            else:
                # Для ошибок типа ValueError (неверный аргумент PUSH или команда)
                raise RuntimeError(f"Error at line {line_idx}: {error_msg}")

    return output

if __name__ == "__main__":
    # Пример использования
    code = """
    PUSH 10
    PUSH 20
    ADD
    PRINT
    # Это комментарий
    PUSH 5
    MUL
    PRINT
    DUP
    PRINT
    SWAP
    POP
    PUSH 2
    DIV
    PRINT
    """
    try:
        results = run(code)
        for res in results:
            print(res)
    except RuntimeError as e:
        print(e)
