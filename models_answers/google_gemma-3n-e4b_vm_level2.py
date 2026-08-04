def run(program: str) -> list[str]:
    """
    Запускает интерпретатор стекового языка с метками и условными переходами и возвращает список выведенных строк.

    Args:
        program: Многострочный текст, представляющий программу на стековом языке.

    Returns:
        Список строк, содержащих вывод оператора PRINT.
    """

    stack = []
    labels = {}
    output = []
    lines = program.splitlines()
    line_number = 1
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        parts = line.split()
        instruction = parts[0]

        if instruction.startswith("LABEL"):
            label_name = instruction.split()[1]
            if label_name in labels:
                output.append(f"Error: Label '{label_name}' already defined on line {line_number}")
            else:
                labels[label_name] = line_number
        elif instruction == "JMP":
            label_name = parts[1]
            if label_name not in labels:
                output.append(f"Error: Label '{label_name}' not defined on line {line_number}")
            else:
                line_number = labels[label_name]
        elif instruction == "JZ":
            label_name = parts[1]
            if label_name not in labels:
                output.append(f"Error: Label '{label_name}' not defined on line {line_number}")
            else:
                operand = stack.pop()
                if operand == 0:
                    line_number = labels[label_name]
        elif instruction == "JNZ":
            label_name = parts[1]
            if label_name not in labels:
                output.append(f"Error: Label '{label_name}' not defined on line {line_number}")
            else:
                operand = stack.pop()
                if operand != 0:
                    line_number = labels[label_name]
        else:
            try:
                if instruction == "PUSH":
                    stack.append(int(parts[1]))
                elif instruction == "POP":
                    if not stack:
                        raise ValueError(f"Stack underflow on line {line_number}")
                    stack.pop()
                elif instruction == "ADD":
                    if len(stack) < 2:
                        raise ValueError(f"Not enough operands for ADD on line {line_number}")
                    operand2 = stack.pop()
                    operand1 = stack.pop()
                    stack.append(operand1 + operand2)
                elif instruction == "SUB":
                    if len(stack) < 2:
                        raise ValueError(f"Not enough operands for SUB on line {line_number}")
                    operand2 = stack.pop()
                    operand1 = stack.pop()
                    stack.append(operand1 - operand2)
                elif instruction == "MUL":
                    if len(stack) < 2:
                        raise ValueError(f"Not enough operands for MUL on line {line_number}")
                    operand2 = stack.pop()
                    operand1 = stack.pop()
                    stack.append(operand1 * operand2)
                elif instruction == "DIV":
                    if len(stack) < 2:
                        raise ValueError(f"Not enough operands for DIV on line {line_number}")
                    operand2 = stack.pop()
                    operand1 = stack.pop()
                    if operand2 == 0:
                        raise ZeroDivisionError(f"Division by zero on line {line_number}")
                    stack.append(operand1 // operand2)  # Integer division
                elif instruction == "DUP":
                    if not stack:
                        raise ValueError(f"Stack is empty, cannot DUP on line {line_number}")
                    stack.append(stack[-1])
                elif instruction == "SWAP":
                    if len(stack) < 2:
                        raise ValueError(f"Not enough elements to SWAP on line {line_number}")
                    stack[-1], stack[-2] = stack[-2], stack[-1]
                elif instruction == "PRINT":
                    if not stack:
                        raise ValueError(f"Stack is empty, cannot PRINT on line {line_number}")
                    output.append(str(stack[-1]))
                else:
                    raise ValueError(f"Unknown instruction: {instruction} on line {line_number}")

            except (ValueError, ZeroDivisionError) as e:
                output.append(str(e))

        line_number = labels.get(line_number, line_number + 1)  # Update line number after label/jump



    return output
