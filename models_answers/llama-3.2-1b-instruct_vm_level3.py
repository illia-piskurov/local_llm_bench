stack = []
lines = program.split('\n')
for i, line in enumerate(lines):
    if line.lstrip().startswith('PUSH'):
        try:
            stack.append(int(line[4:]))
        except ValueError:
            print(f"Error on line {i+1}")
    elif line.lstrip().startswith('POP'):
        if not stack:
            print(f"Error on line {i+1}")
            continue
        else:
            stack.pop()
    elif line.lstrip().startswith('ADD'):
        try:
            a = stack[-2]
            b = stack[-1]
            stack.append(a + b)
        except IndexError:
            print(f"Error on line {i+1}")
    elif line.lstrip().startswith('SUB'):
        try:
            a = stack[-2]
            b = stack[-1]
            if b == 0:
                raise ZeroDivisionError
            stack.append(a - b)
        except ValueError:
            print(f"Error on line {i+1}")
    elif line.lstrip().startswith('MUL'):
        try:
            a = stack[-2]
            b = stack[-1]
            stack.append(a * b)
        except IndexError:
            print(f"Error on line {i+1}")
    elif line.lstrip().startswith('DIV'):
        try:
            b, a = map(int, line.split())
            if a == 0:
                raise ZeroDivisionError
            stack.append(a // b)
        except ValueError:
            print(f"Error on line {i+1}")
    elif line.lstrip().startswith('DUP'):
        if not stack:
            print(f"Error on line {i+1}")
            continue
        else:
            stack.append(stack[-1])
    elif line.lstrip().startswith('SWAP'):
        try:
            a, b = map(int, line.split())
            stack.append(b)
            stack.append(a)
        except ValueError:
            print(f"Error on line {i+1}")
    elif line.lstrip().startswith('PRINT'):
        if not stack:
            print(f"Error on line {i+1}")
            continue
        else:
            return [f'PRINT {stack.pop()}']
    elif line.startswith('LABEL'):
        name = line.split()[1]
        try:
            while True:
                if line in lines[i:i+4]:
                    break
                i += 1
        except IndexError:
            print(f"Error on line {i+1}")
    elif line.startswith('JMP'):
        label_name = line[3:]
        try:
            while True:
                if line in lines[i:i+4]:
                    break
                i += 1
        except IndexError:
            print(f"Error on line {i+1}")
    elif line.startswith('JZ'):
        label_name = line[2:]
        try:
            while True:
                if line in lines[i:i+4]:
                    break
                i += 1
        except IndexError:
            print(f"Error on line {i+1}")
    elif line.startswith('JNZ'):
        label_name = line[3:]
        try:
            while True:
                if line in lines[i:i+4]:
                    break
                i += 1
        except IndexError:
            print(f"Error on line {i+1}")

def run(program: str) -> list[str]:
    stack = []
    lines = program.split('\n')
    for i, line in enumerate(lines):
        if line.lstrip().startswith('PUSH'):
            try:
                stack.append(int(line[4:]))
            except ValueError:
                print(f"Error on line {i+1}")
        elif line.lstrip().startswith('POP'):
            if not stack:
                print(f"Error on line {i+1}")
                continue
            else:
                stack.pop()
        elif line.lstrip().startswith('ADD'):
            try:
                a = stack[-2]
                b = stack[-1]
                stack.append(a + b)
            except IndexError:
                print(f"Error on line {i+1}")
        elif line.lstrip().startswith('SUB'):
            try:
                a = stack[-2]
                b = stack[-1]
                if b == 0:
                    raise ZeroDivisionError
                stack.append(a - b)
            except ValueError:
                print(f"Error on line {i+1}")
        elif line.lstrip().startswith('MUL'):
            try:
                a = stack[-2]
                b = stack[-1]
                stack.append(a * b)
            except IndexError:
                print(f"Error on line {i+1}")
        elif line.lstrip().startswith('DIV'):
            try:
                b, a = map(int, line.split())
                if a == 0:
                    raise ZeroDivisionError
                stack.append(a // b)
            except ValueError:
                print(f"Error on line {i+1}")
        elif line.lstrip().startswith('DUP'):
            if not stack:
                print(f"Error on line {i+1}")
                continue
            else:
                stack.append(stack[-1])
        elif line.lstrip().startswith('SWAP'):
            try:
                a, b = map(int, line.split())
                stack.append(b)
                stack.append(a)
            except ValueError:
                print(f"Error on line {i+1}")
        elif line.lstrip().startswith('PRINT'):
            if not stack:
                print(f"Error on line {i+1}")
                continue
            else:
                return [f'PRINT {stack.pop()}']
    while True:
        if lines[i] in ['JMP', 'JZ', 'JNZ']:
            label_name = lines[i][3:]
            try:
                i += 4
            except IndexError:
                print(f"Error on line {i+1}")
        elif lines[i].startswith('LABEL'):
            name = lines[i].split()[1]
            while True:
                if lines[i] in lines[i:i+4]:
                    break
                i += 1
    return [f'PRINT {stack.pop()}' for _ in range(len(lines) - i)]

User: Дополни свою реализацию поддержкой подпрограмм, операций сравнения и именованных переменных:

1. Подпрограммы (стек вызовов):
   CALL <name>  — сохранить адрес возврата в стек вызовов и перейти к метке <name>
   RET          — снять адрес возврата со стека вызовов и перейти к нему (к инструкции, следующей сразу за CALL).
                  Если стек вызовов пуст — кинуть понятную ошибку.

2. Операции сравнения:
   EQ           — снять два значения (b, затем a), положить 1, если a == b, иначе 0
   GT           — снять два значения (b, затем a), положить 1, если a > b, иначе 0
   LT           — снять два значения (b, затем a), положить 1, если a < b, иначе 0

3. Именованные переменные (память):
   STORE <var>  — снять значение со стека и сохранить в переменную <var>
   LOAD <var>   — положить значение переменной <var> на стек. Если переменная <var> ещё не была сохранена — кинуть понятную ошибку.

Требования:
- Поддержка вложенных и rekursiveх вызовов подпрограмм через CALL/RET.
-Не меняй поведение уже реализованных инструкций и сохрани сигнатуру run(program: str) -> list[str].

В ответе верни только код одним блоком
