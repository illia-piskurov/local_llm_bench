import sys

def run(program: str) -> list[str]:
    """
    Интерпретирует программу стекового языка, поддерживая метки и условные переходы.

    Args:
        program: Многострочный текст с инструкциями.

    Returns:
        Список строк, содержащих вывод команды PRINT.

    Raises:
        RuntimeError: Если произошла ошибка выполнения (нехватка данных на стеке, деление на ноль, неизвестная метка).
    """
    stack = []
    output = []
    lines = program.split('\n')
    labels = {}  # Словарь для хранения {имя_метки: индекс_строки}

    # --- Первый проход: Сбор всех меток ---
    for i, line in enumerate(lines):
        stripped_line = line.strip()
        if not stripped_line or stripped_line.startswith('#'):
            continue

        tokens = stripped_line.split()
        if tokens and tokens[0] == "LABEL":
            label_name = tokens[1]
            if label_name in labels:
                raise RuntimeError(f"Ошибка в строке {i + 1}: Метка '{label_name}' уже определена.")
            labels[label_name] = i

    # --- Второй проход: Выполнение программы ---
    current_index = 0
    while current_index < len(lines):
        line = lines[current_index]
        line_number = current_index + 1
        stripped_line = line.strip()

        # Игнорирование пустых строк и комментариев
        if not stripped_line or stripped_line.startswith('#'):
            current_index += 1
            continue

        tokens = stripped_line.split()
        if not tokens:
            current_index += 1
            continue

        instruction = tokens[0]
        next_index = current_index + 1 # По умолчанию, идем на следующую строку

        try:
            # --- Инструкции управления потоком ---
            if instruction == "LABEL":
                # LABEL <name> - просто регистрирует метку (уже сделано выше)
                pass

            elif instruction == "JMP":
                target_label = tokens[1]
                if target_label not in labels:
                    raise NameError(f"Неизвестная метка перехода: {target_label}")
                next_index = labels[target_label] # Устанавливаем индекс прыжка

            elif instruction == "JZ":
                target_label = tokens[1]
                if target_label not in labels:
                    raise NameError(f"Неизвестная метка перехода: {target_label}")
                if len(stack) < 1:
                    raise IndexError("Недостаточно элементов на стеке для JZ.")

                condition = stack.pop()
                if condition == 0:
                    next_index = labels[target_label] # Успешный переход
                else:
                    # Не переходим, просто продолжаем выполнение с next_index
                    pass

            elif instruction == "JNZ":
                target_label = tokens[1]
                if target_label not in labels:
                    raise NameError(f"Неизвестная метка перехода: {target_label}")
                if len(stack) < 1:
                    raise IndexError("Недостаточно элементов на стеке для JNZ.")

                condition = stack.pop()
                if condition != 0:
                    next_index = labels[target_label] # Успешный переход
                else:
                    # Не переходим, просто продолжаем выполнение с next_index
                    pass

            # --- Стандартные инструкции стека ---
            elif instruction == "PUSH":
                if len(tokens) != 2:
                    raise ValueError("PUSH требует один аргумент.")
                value = int(tokens[1])
                stack.append(value)

            elif instruction == "POP":
                if not stack:
                    raise IndexError("Недостаточно элементов на стеке для POP.")
                stack.pop()

            elif instruction == "DUP":
                if not stack:
                    raise IndexError("Недостаточно элементов на стеке для DUP.")
                stack.append(stack[-1])

            elif instruction == "SWAP":
                if len(stack) < 2:
                    raise IndexError("Недостаточно элементов на стеке для SWAP (требуется минимум 2).")
                a = stack.pop()
                b = stack.pop()
                stack.append(a)
                stack.append(b)

            elif instruction == "PRINT":
                if not stack:
                    raise IndexError("Недостаточно элементов на стеке для PRINT.")
                output.append(str(stack[-1]))

            # --- Бинарные операции ---
            elif instruction in ["ADD", "SUB", "MUL", "DIV"]:
                if len(stack) < 2:
                    raise IndexError(f"Недостаточно элементов на стеке для {instruction} (требуется минимум 2).")

                b = stack.pop()
                a = stack.pop()
                result = None

                if instruction == "ADD":
                    result = a + b
                elif instruction == "SUB":
                    result = a - b
                elif instruction == "MUL":
                    result = a * b
                elif instruction == "DIV":
                    if b == 0:
                        raise ZeroDivisionError("Деление на ноль.")
                    # Целочисленное деление (a // b)
                    result = a // b

                stack.append(result)

            else:
                raise NameError(f"Неизвестная инструкция: {instruction}")

        except IndexError as e:
            raise RuntimeError(f"Ошибка в строке {line_number}: {e}")
        except ZeroDivisionError as e:
            raise RuntimeError(f"Ошибка в строке {line_number}: Деление на ноль.")
        except (ValueError, NameError) as e:
             # Ошибки парсинга или неизвестных меток
            raise RuntimeError(f"Ошибка в строке {line_number}: {e}")

        # Обновляем индекс для следующей итерации. 
        # Если произошел прыжок (JMP, JZ, JNZ), next_index уже установлен на целевой адрес.
        current_index = next_index

    return output

if __name__ == '__main__':
    # --- Тест 1: Условный переход (JZ) ---
    program_jz_test = """
    PUSH 0
    LABEL start
    PUSH 5
    PUSH 3
    ADD       # Stack: [8]
    PRINT     # Output: 8

    PUSH 0   # Проверяемое значение для JZ
    JZ skip  # Если 0, переходим к skip. Так как 0 == 0, прыгаем.
    JMP end  # Этот код не должен выполниться

skip:
    PRINT     # Output: 1 (потому что мы сбросили стек и добавили 1)

end:
    PUSH 99 # Должно быть пропущено
    """
    print("--- Тест 1 (JZ - Успешный переход) ---")
    try:
        results = run(program_jz_test)
        # Ожидаемый вывод: ['8', '1']
        print("Вывод:", results)
    except RuntimeError as e:
        print("Ошибка выполнения:", e)

    # --- Тест 2: Условный переход (JNZ) и цикл ---
    program_jnz_test = """
    PUSH 5   # Инициализация счетчика
    LABEL loop_start
    DUP       # Stack: [5, 5]
    PUSH 1
    SUB       # Stack: [4] (Счетчик уменьшается)

    PUSH 0
    JNZ loop_start # Пока не 0, продолжаем цикл. Pop'ит текущее значение (например, 4).

    PRINT     # Вывод финального значения счетчика
    """
    print("\n--- Тест 2 (JNZ - Цикл) ---")
    try:
        results = run(program_jnz_test)
        # Ожидаемый вывод: ['0'] (Счетчик дошел до нуля, и мы выводим его)
        print("Вывод:", results)
    except RuntimeError as e:
        print("Ошибка выполнения:", e)

    # --- Тест 3: Безусловный переход (JMP) ---
    program_jmp_test = """
    PUSH 10
    LABEL start
    ADD       # Эта инструкция должна быть пропущена
    JMP end   # Прыгаем к концу

end:
    PRINT     # Вывод 10, так как ADD не выполнился.
    """
    print("\n--- Тест 3 (JMP - Пропуск кода) ---")
    try:
        results = run(program_jmp_test)
        # Ожидаемый вывод: ['10']
        print("Вывод:", results)
    except RuntimeError as e:
        print("Ошибка выполнения:", e)

    # --- Тест 4: Неизвестная метка ---
    program_error = """
    PUSH 1
    JMP missing_label
    """
    print("\n--- Тест 4 (Error - Missing Label) ---")
    try:
        run(program_error)
    except RuntimeError as e:
        print("Перехвачена ошибка:", e)
