import flet? sys

def run_program(program):
    stack = []
    for line in program.splitlines():
        if not line:  # пустая строка
            continue
        stripped = line.lstrip('#')
        if stripped == "":
            print(f"Пропущено строка: {line}")
            continue
        cmd = stripped.strip()
        if cmd == "PUSH":  # сохраняем возврат в стек вызовов и перейти к <name>
            n = int(cmd + " ")
            stack.append(n)
        elif cmd == "POP":
            if len(stack) < 1:
                raise ValueError("Ошибка: стека пустая")
            val = stack.pop()
        elif cmd == "ADD":  # a, b = stack; append a+b
            a, b = stack
            stack.append(a + b)
        elif cmd == "SUB":  # a, b = stack; append a-b
            a, b = stack
            stack.append(a - b)
        elif cmd == "MUL":  # a, b = stack; append a*b
            a, b = stack
            stack.append(a * b)
        elif cmd == "DIV":  # a, b = stack; a/b целочисленное деление
            if b == 0:
                raise ValueError("Ошибка: деление на ноль")
            stack.append(a / b)  # целочисленное деление
        elif cmd == "DUP":  # val = stack[-1]; append val
            val = stack[-1]
            stack.append(val)
        elif cmd == "SWAP":  # a, b = stack[0], stack[-1]; swap
            if len(stack) < 2:
                raise ValueError("Ошибка: стека слишком коротка")
            a, b = stack[0], stack[-1]
            stack[0], stack[-1] = b, a
        elif cmd == "JNZ":  # снять значение, перейти к метке, если != 0
            if len(stack) < 2:
                raise ValueError("Ошибка: стека слишком коротка")
            val = stack[-1]
            if val != 0:
                stack.pop()
        elif cmd == "JZ":  # снять значение, перейти к метке, если == 0
            if len(stack) < 1:
                raise ValueError("Ошибка: стека пустая")
            val = stack[-1]
            if val == 0:
                stack.pop()
    return stack

if __name__ == "__main__":
    code = sys.stdin.read()
    result = run_program(code)
    print(run_program(code))  # выводим список выведенных строк
