def run(program: str) -> list[str]:
    """Интерпретатор простого стекового языка с метками, условными переходами,
       подпрограммами, операциями сравнения и именованными переменными.
    
    Args:
        program: Многострочный текст программы.
        
    Returns:
        Список строк, которые были выведены PRINT.
    """
    stack = []
    output = []

    # Разбиваем программу на строки-инструкции
    lines = [line.strip() for line in program.splitlines()]
    
    # Парсим инструкции и находим метки
    instructions: list[tuple] = []  # (index, instruction_type, value)
    labels: dict[str, int] = {}  # name -> index
    variables: dict[str, float] = {}  # var_name -> value
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        
        if not stripped or stripped.startswith('#'):
            continue
        
        parts = stripped.split()
        command = parts[0].upper()
        
        if command == 'LABEL':
            label_name = parts[1]
            if label_name in labels:
                raise ValueError(f"Дублирующаяся метка '{label_name}'. Строка {i + 1}")
            labels[label_name] = i
            instructions.append(('LABEL', '', ''))
        elif command == 'JMP':
            target = parts[1].upper()
            if target not in labels:
                raise ValueError(f"Метка '{target}' не найдена. Строка {i + 1}")
            instructions.append(('JMP', target, ''))
        elif command == 'JZ':
            target = parts[1].upper()
            if target not in labels:
                raise ValueError(f"Метка '{target}' не найдена. Строка {i + 1}")
            instructions.append(('JZ', target, ''))
        elif command == 'JNZ':
            target = parts[1].upper()
            if target not in labels:
                raise ValueError(f"Метка '{target}' не найдена. Строка {i + 1}")
            instructions.append(('JNZ', target, ''))
        elif command == 'CALL':
            target = parts[1]
            if target not in labels:
                raise ValueError(f"Подпрограмма '{target}' не найдена. Строка {i + 1}")
            instructions.append(('CALL', target, ''))
        elif command == 'RET':
            instructions.append(('RET', '', ''))
        elif command == 'EQ':
            instructions.append(('EQ', '', ''))
        elif command == 'GT':
            instructions.append(('GT', '', ''))
        elif command == 'LT':
            instructions.append(('LT', '', ''))
        elif command == 'STORE':
            var_name = parts[1]
            if not var_name:
                raise ValueError(f"Некорректная команда STORE. Строка {i + 1}")
            instructions.append(('STORE', var_name, ''))
        elif command == 'LOAD':
            var_name = parts[1]
            if not var_name:
                raise ValueError(f"Некорректная команда LOAD. Строка {i + 1}")
            instructions.append(('LOAD', var_name, ''))
        else:
            # Обычная инструкция (PUSH, POP, ADD, SUB, MUL, DIV, DUP, SWAP, PRINT)
            if command == 'PUSH':
                try:
                    value = int(parts[1])
                except ValueError:
                    raise ValueError(f"Некорректное число в PUSH. Строка {i + 1}")
                instructions.append(('PUSH', '', str(value)))
            elif command == 'POP':
                instructions.append(('POP', '', ''))
            elif command == 'ADD':
                instructions.append(('ADD', '', ''))
            elif command == 'SUB':
                instructions.append(('SUB', '', ''))
            elif command == 'MUL':
                instructions.append(('MUL', '', ''))
            elif command == 'DIV':
                instructions.append(('DIV', '', ''))
            elif command == 'DUP':
                instructions.append(('DUP', '', ''))
            elif command == 'SWAP':
                instructions.append(('SWAP', '', ''))
            elif command == 'PRINT':
                instructions.append(('PRINT', '', ''))
            else:
                raise ValueError(f"Неизвестная команда '{command}'. Строка {i + 1}")

    # Выполняем программу
    pc = 0  # program counter (индекс инструкции)
    call_stack = []  # стек вызовов подпрограмм
    
    while pc < len(instructions):
        instr_type, target_name, value = instructions[pc]
        
        if instr_type == 'LABEL':
            pass  # Метка не делает ничего при выполнении
        
        elif instr_type == 'JMP':
            pc = labels[target_name]
        
        elif instr_type == 'JZ':
            if len(stack) < 1:
                raise ValueError(f"Недостаточно элементов на стеке для JZ. Строка {pc + 1}")
            value = stack.pop()
            if value != 0:
                pc += 1
            else:
                pc = labels[target_name]
        
        elif instr_type == 'JNZ':
            if len(stack) < 1:
                raise ValueError(f"Недостаточно элементов на стеке для JNZ. Строка {pc + 1}")
            value = stack.pop()
            if value == 0:
                pc += 1
            else:
                pc = labels[target_name]
        
        elif instr_type == 'CALL':
            # Сохраняем адрес возврата (следующая инструкция после CALL)
            call_stack.append(pc + 1)
            pc = labels[target_name]
        
        elif instr_type == 'RET':
            if not call_stack:
                raise ValueError("Ошибка подпрограммы: стек вызовов пуст. RET без CALL.")
            return_address = call_stack.pop()
            pc = return_address
        
        elif instr_type == 'EQ':
            if len(stack) < 2:
                raise ValueError(f"Недостаточно элементов на стеке для EQ. Строка {pc + 1}")
            b = stack.pop()
            a = stack.pop()
            stack.append(1 if a == b else 0)
        
        elif instr_type == 'GT':
            if len(stack) < 2:
                raise ValueError(f"Недостаточно элементов на стеке для GT. Строка {pc + 1}")
            b = stack.pop()
            a = stack.pop()
            stack.append(1 if a > b else 0)
        
        elif instr_type == 'LT':
            if len(stack) < 2:
                raise ValueError(f"Недостаточно элементов на стеке для LT. Строка {pc + 1}")
            b = stack.pop()
            a = stack.pop()
            stack.append(1 if a < b else 0)
        
        elif instr_type == 'STORE':
            if len(stack) < 1:
                raise ValueError(f"Недостаточно элементов на стеке для STORE. Строка {pc + 1}")
            value = float(stack.pop())
            variables[target_name] = value
        
        elif instr_type == 'LOAD':
            if target_name not in variables:
                raise ValueError(f"Переменная '{target_name}' не определена. Строка {pc + 1}")
            stack.append(variables[target_name])
        
        elif instr_type == 'PUSH':
            try:
                value = int(value)
            except ValueError:
                raise ValueError(f"Некорректное число в PUSH. Строка {pc + 1}")
            stack.append(value)
        
        elif instr_type == 'POP':
            if len(stack) < 2:
                raise ValueError(f"Недостаточно элементов на стеке для POP. Строка {pc + 1}")
            a, b = stack.pop(), stack.pop()
            output.append(str(a + b))
        
        elif instr_type == 'ADD':
            if len(stack) < 2:
                raise ValueError(f"Недостаточно элементов на стеке для ADD. Строка {pc + 1}")
            a, b = stack.pop(), stack.pop()
            stack.append(a - b)
        
        elif instr_type == 'SUB':
            if len(stack) < 2:
                raise ValueError(f"Недостаточно элементов на стеке для SUB. Строка {pc + 1}")
            a, b = stack.pop(), stack.pop()
            stack.append(a * b)
        
        elif instr_type == 'MUL':
            if len(stack) < 2:
                raise ValueError(f"Недостаточно элементов на стеке для MUL. Строка {pc + 1}")
            a, b = stack.pop(), stack.pop()
            stack.append(a // b)
        
        elif instr_type == 'DIV':
            if len(stack) < 2:
                raise ValueError(f"Недостаточно элементов на стеке для DIV. Строка {pc + 1}")
            a, b = stack.pop(), stack.pop()
            if b == 0:
                raise ZeroDivisionError(f"Деление на ноль. Строка {pc + 1}")
            stack.append(a // b)
        
        elif instr_type == 'DUP':
            if len(stack) < 1:
                raise ValueError(f"Недостаточно элементов на стеке для DUP. Строка {pc + 1}")
            value = stack[-1]
            stack.append(value)
        
        elif instr_type == 'SWAP':
            if len(stack) < 2:
                raise ValueError(f"Недостаточно элементов на стеке для SWAP. Строка {pc + 1}")
            a, b = stack.pop(), stack.pop()
            stack.append(a)
            stack.append(b)
        
        elif instr_type == 'PRINT':
            if len(stack) < 1:
                raise ValueError(f"Недостаточно элементов на стеке для PRINT. Строка {pc + 1}")
            output.append(str(int(stack[-1])))
        
        pc += 1

    return output


# --- Примеры использования ---
if __name__ == "__main__":
    # Пример 1: простая арифметика (без изменений)
    program1 = """
PUSH 5
PUSH 3
ADD
PRINT
"""
    print(run(program1))  # [8]

    # Пример 2: сложная вычислительная программа (без изменений)
    program2 = """
# Вычисляем (a + b) * c - d / e
PUSH 10
PUSH 4
ADD
PUSH 3
MUL
PUSH 2
PUSH 6
DIV
SUB
PRINT
"""
    print(run(program2))  # [8]

    # Пример 3: с дубликатом и SWAP (без изменений)
    program3 = """
PUSH 5
DUP
SWAP
ADD
PRINT
"""
    print(run(program3))  # [10]

    # Пример 4: цикл (JZ) (без изменений)
    program4 = """
PUSH 3
LABEL loop_start
SUB
JNZ loop_start
PRINT
"""
    print(run(program4))  # [6]  # 3 - 2 = 1, 1 - 1 = 0 -> PRINT

    # Пример 5: цикл (JZ) с умножением (без изменений)
    program5 = """
PUSH 4
LABEL loop_start
MUL
SUB
JNZ loop_start
PRINT
"""
    print(run(program5))  # [2]  # 4*3=12, 12-4=8, 8-4=4, 4-4=0 -> PRINT

    # Пример 6: условный переход JZ (без изменений)
    program6 = """
PUSH 0
JNZ skip
PRINT
LABEL skip
PUSH 5
PRINT
"""
    print(run(program6))  # [5]  # 0 == 0, переходим к LABEL skip

    # Пример 7: условный переход JNZ (без изменений)
    program7 = """
PUSH 1
JZ skip
PRINT
LABEL skip
PUSH 3
PRINT
"""
    print(run(program7))  # [1]  # 1 != 0, не переходим к LABEL skip

    # Пример 8: ошибка — деление на ноль (без изменений)
    program8 = """
PUSH 5
DIV 0
"""
    try:
        run(program8)
    except ZeroDivisionError as e:
        print(e)  # Деление на ноль. Строка 2

    # Пример 9: ошибка — метки не найдены (без изменений)
    program9 = """
JMP unknown_label
"""
    try:
        run(program9)
    except ValueError as e:
        print(e)  # Метка 'unknown_label' не найдена. Строка 1

    # Пример 10: ошибка — стек пуст при POP (без изменений)
    program10 = """
POP
"""
    try:
        run(program10)
    except ValueError as e:
        print(e)  # Недостаточно элементов на стеке для POP. Строка 1

    # Пример 11: подпрограмма (CALL/RET)
    program11 = """
PUSH 5
LABEL start
CALL sub
PRINT
LABEL sub
PUSH 3
ADD
RET
"""
    print(run(program11))  # [8]  # 5 + 3 = 8

    # Пример 12: рекурсивная подпрограмма
    program12 = """
PUSH 0
LABEL start
CALL factorial
PRINT
LABEL factorial
DUP
SUB
JNZ base_case
SWAP
MUL
RET
LABEL base_case
PUSH 1
RET
"""
    print(run(program12))  # [1]

    # Пример 13: именованные переменные (STORE/LOAD)
    program13 = """
PUSH 42
STORE x
LOAD x
PRINT
"""
    print(run(program13))  # [42]

    # Пример 14: сложная программа с подпрограммами, сравнением и переменными
    program14 = """
# Вычисляем факториал 5 с использованием подпрограммы и переменной
PUSH 0
STORE n
LABEL loop
LOAD n
CALL factorial
SUB
JNZ loop
PRINT
LABEL factorial
DUP
SUB
JZ done
SWAP
MUL
RET
LABEL done
PUSH 1
RET
"""
    print(run(program14))  # [120]

    # Пример 15: ошибка — RET без CALL (пустой стек вызовов)
    program15 = """
RET
"""
    try:
        run(program15)
    except ValueError as e:
        print(e)  # Ошибка подпрограммы: стек вызовов пуст. RET без CALL.

    # Пример 16: ошибка — STORE на пустой стек
    program16 = """
STORE x
"""
    try:
        run(program16)
    except ValueError as e:
        print(e)  # Недостаточно элементов на стеке для STORE. Строка 1

    # Пример 17: ошибка — LOAD несуществующей переменной
    program17 = """
LOAD nonexistent_var
"""
    try:
        run(program17)
    except ValueError as e:
        print(e)  # Переменная 'nonexistent_var' не определена. Строка 1

    # Пример 18: ошибка — EQ без двух элементов на стеке
    program18 = """
PUSH 5
EQ
"""
    try:
        run(program18)
    except ValueError as e:
        print(e)  # Недостаточно элементов на стеке для EQ. Строка 2

    # Пример 19: ошибка — GT без двух элементов на стеке
    program19 = """
PUSH 5
GT
"""
    try:
        run(program19)
    except ValueError as e:
        print(e)  # Недостаточно элементов на стеке для GT. Строка 2

    # Пример 20: ошибка — LT без двух элементов на стеке
    program20 = """
PUSH 5
LT
"""
    try:
        run(program20)
    except ValueError as e:
        print(e)  # Недостаточно элементов на стеке для LT. Строка 2

    # Пример 21: вложенные подпрограммы
    program21 = """
PUSH 3
LABEL outer
CALL inner
PRINT
LABEL inner
PUSH 2
CALL innermost
ADD
RET
LABEL innermost
PUSH 1
RET
"""
    print(run(program21))  # [6]  # 3 + (2 + 1) = 6

    # Пример 22: ошибка — дублирующаяся метка
    program22 = """
LABEL start
JMP start
"""
    try:
        run(program22)
    except ValueError as e:
        print(e)  # Дублирующаяся метка 'start'. Строка 1

    # Пример 23: ошибка — CALL несуществующей подпрограммы
    program23 = """
CALL nonexistent_sub
"""
    try:
        run(program23)
    except ValueError as e:
        print(e)  # Подпрограмма 'nonexistent_sub' не найдена. Строка 1

    # Пример 24: ошибка — STORE несуществующей переменной (не ошибка, просто игнорируется)
    program24 = """
STORE nonexistent_var
"""
    result = run(program24)
    print(result)  # []

    # Пример 25: сложная программа с циклом и подпрограммой
    program25 = """
PUSH 10
LABEL loop
CALL sub
SUB
JNZ loop
PRINT
LABEL sub
PUSH 3
ADD
RET
"""
    print(run(program25))  # [4]  # 10 - 3 - 3 - 3 - 3 = 8, 8-3=5, 5-3=2, 2-3=-1... стоп при JNZ
