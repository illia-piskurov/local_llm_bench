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
                if a == 0 or b == 0:
                    output.append("")
                else:
                    result = a + b
                    output.append(str(result))
            except (IndexError, ValueError):
                print(f"Error: ADD at line {line_num}")
        elif cmd == 'SUB':
            try:
                a = stack.pop()
                b = stack.pop()
                if b == 0:
                    output.append("")
                else:
                    result = a - b
                    output.append(str(result))
            except (IndexError, ValueError):
                print(f"Error: SUB at line {line_num}")
        elif cmd == 'MUL':
            try:
                a = stack.pop()
                b = stack.pop()
                if b == 0:
                    output.append("")
                else:
                    result = a * b
                    output.append(str(result))
            except (IndexError, ValueError):
                print(f"Error: MUL at line {line_num}")
        elif cmd == 'DIV':
            try:
                b = stack.pop()
                a = stack.pop()
                if b == 0:
                    print(f"Error: DIV at line {line_num}: Division by zero")
                    continue
                result = a / b
                output.append(str(result))
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
        elif cmd == 'PRINT_MET':
            if stack.peek() == "JMP":
                continue
            else:
                output.append(stack.peek())
        elif cmd == 'JMP':
            if len(stack.items) < 2:
                print(f"Error: JMP at line {line_num}")
                continue
            label = stack.peek()
            index = int(stack.pop())
            if label == str(index):
                continue
            stack.push(label)
            output.append("")
        elif cmd == 'LABEL':
            label = stack.peek()
            if label == "JMP":
                continue
            stack.push(label)
            output.append("")
        elif cmd == 'PRINT':
            if not stack.is_empty():
                output.append(stack.peek())
            else:
                output.append("")
        elif cmd == 'CALL':
            if len(stack.items) < 2:
                print(f"Error: CALL at line {line_num}")
                continue
            try:
                label = stack.pop()
                arg = stack.pop(0)
                if isinstance(arg, int):
                    stack.push(label)
                    stack.push(arg)
                else:
                    stack.push(stack.peek())
            except IndexError:
                print(f"Error: CALL at line {line_num}")
        elif cmd == 'RET':
            try:
                index = stack.pop()
                if 0 <= index < stack.size():
                    stack.push(stack.peek())
                    output.append(str(index))
                else:
                    print(f"Error: RET at line {line_num}")
            except IndexError:
                print(f"Error: RET at line {line_num}")
        elif cmd == 'RET_VALUE':
            try:
                value = stack.pop()
                output.append(str(value))
            except IndexError:
                print(f"Error: RET_VALUE at line {line_num}")
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
