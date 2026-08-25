class Stack:
    def __init__(self):
        self.items = []

    def is_empty(self):
        return len(self.items) == 0

    def push(self, item):
        self.items.append(item)

    def pop(self):
        if not self.is_empty():
            return self.items.pop()
        raise IndexError("pop from empty stack")

    def peek(self):
        if not self.is_empty():
            return self.items[-1]
        raise IndexError("peek from empty stack")

    def size(self):
        return len(self.items)

def interpreter(program):
    stack = Stack()
    lines = program.split('\n')
    output = []
    line_num = 0
    for line in lines:
        line_num += 1
        if line.startswith('#'):
            continue
        parts = line.split()
        cmd = parts[0]
        if cmd == 'PUSH':
            try:
                value = int(parts[1])
                stack.push(value)
            except IndexError:
                print(f"Error: PUSH at line {line_num}")
        elif cmd == 'POP':
            try:
                val = stack.pop()
                output.append(str(val))
            except IndexError:
                print(f"Error: POP at line {line_num}")
        elif cmd == 'ADD':
            try:
                a = stack.pop()
                b = stack.pop()
                output.append(str(a + b))
            except (IndexError, ValueError):
                print(f"Error: ADD at line {line_num}")
        elif cmd == 'SUB':
            try:
                a = stack.pop()
                b = stack.pop()
                output.append(str(a - b))
            except (IndexError, ValueError):
                print(f"Error: SUB at line {line_num}")
        elif cmd == 'MUL':
            try:
                a = stack.pop()
                b = stack.pop()
                output.append(str(a * b))
            except (IndexError, ValueError):
                print(f"Error: MUL at line {line_num}")
        elif cmd == 'DIV':
            try:
                b = stack.pop()
                a = stack.pop()
                if b == 0:
                    print(f"Error: DIV at line {line_num}: Division by zero")
                    continue
                output.append(str(a / b))
            except (IndexError, ValueError):
                print(f"Error: DIV at line {line_num}")
        elif cmd == 'DUP':
            stack.push(stack.peek())
            output.append("")
        elif cmd == 'SWAP':
            if len(stack.items) < 2:
                print(f"Error: SWAP at line {line_num}: Not enough elements on stack")
                continue
            a = stack.pop()
            b = stack.pop()
            stack.push(a)
            stack.push(b)
            output.append("")
        elif cmd == 'PRINT':
            if not stack.is_empty():
                output.append(stack.peek())
            else:
                output.append("")
        elif cmd == 'JMP':
            # Переход к следующей метке
            pass
        elif cmd == 'LABEL':
            # Обработка метки — просто сохраняем её для дальнейшего использования
            pass
        elif cmd == 'PRINT_MET':
            # Обработка метки с текстом
            if stack.peek() == "JMP":
                # Переход к следующей строке после JMP
                continue
            else:
                output.append(stack.peek())
        elif cmd == 'JZ':
            try:
                index = int(parts[1])
                if 0 <= index < stack.size():
                    line_num = index
                    continue
                print(f"Error: JZ at line {line_num}")
            except (IndexError, ValueError):
                pass
        elif cmd == 'JNZ':
            try:
                index = int(parts[1])
                if 0 <= index < stack.size():
                    line_num = index
                    continue
                print(f"Error: JNZ at line {line_num}")
            except (IndexError, ValueError):
                pass
        else:
            print(f"Unknown command or label at line {line_num}")
    return output
