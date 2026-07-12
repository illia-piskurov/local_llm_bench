class Interpreter:
    def __init__(self):
        self.stack = []
        self.output = []
        self.labels = {}
        self.program_counter = 0

    def run(self, program: str) -> list[str]:
        lines = [line.strip() for line in program.split('\n') if line and not line.startswith('#')]
        for i, line in enumerate(lines, start=1):
            self.execute(line, i)
        return self.output

    def execute(self, line: str, line_number: int) -> None:
        tokens = line.split()
        if len(tokens) == 0:
            raise ValueError(f"Некорректная строка {line_number}")
        
        command = tokens[0]
        if command == 'PUSH':
            try:
                value = int(tokens[1])
                self.stack.append(value)
            except ValueError as e:
                raise ValueError(f"Некорректный аргумент в строке {line_number}: {e}")
        elif command == 'POP':
            if not self.stack:
                raise ValueError(f"Стек пуст в строке {line_number}")
            self.stack.pop()
        elif command in ['ADD', 'SUB', 'MUL', 'DIV']:
            if len(self.stack) < 2:
                raise ValueError(f"Недостаточно элементов на стеке в строке {line_number}")
            b = self.stack.pop()
            a = self.stack.pop()
            if command == 'ADD':
                result = a + b
            elif command == 'SUB':
                result = a - b
            elif command == 'MUL':
                result = a * b
            elif command == 'DIV':
                if b == 0:
                    raise ValueError(f"Деление на ноль в строке {line_number}")
                result = a // b
            self.stack.append(result)
        elif command == 'DUP':
            if not self.stack:
                raise ValueError(f"Стек пуст в строке {line_number}")
            self.stack.append(self.stack[-1])
        elif command == 'SWAP':
            if len(self.stack) < 2:
                raise ValueError(f"Недостаточно элементов на стеке в строке {line_number}")
            b = self.stack.pop()
            a = self.stack.pop()
            self.stack.extend([a, b])
        elif command == 'PRINT':
            if not self.stack:
                raise ValueError(f"Стек пуст в строке {line_number}")
            value = self.stack[-1]
            self.output.append(str(value))
        elif command == 'LABEL':
            label_name = tokens[1]
            if label_name in self.labels:
                raise ValueError(f"Дубликат метки '{label_name}'")
            self.labels[label_name] = self.program_counter
        elif command == 'JMP':
            label_name = tokens[1]
            if label_name not in self.labels:
                raise ValueError(f"Нет метки '{label_name}'")
            self.program_counter = self.labels[label_name]
        elif command == 'JZ':
            if len(self.stack) < 1:
                raise ValueError(f"Недостаточно элементов на стеке в строке {line_number}")
            value = self.stack.pop()
            label_name = tokens[1]
            if value != 0:
                if label_name not in self.labels:
                    raise ValueError(f"Нет метки '{label_name}'")
                self.program_counter = self.labels[label_name]
        elif command == 'JNZ':
            if len(self.stack) < 1:
                raise ValueError(f"Недостаточно элементов на стеке в строке {line_number}")
            value = self.stack.pop()
            label_name = tokens[1]
            if value != 0:
                if label_name not in self.labels:
                    raise ValueError(f"Нет метки '{label_name}'")
                self.program_counter = self.labels[label_name]
        else:
            raise ValueError(f"Недопустимая команда в строке {line_number}")
        
        self.program_counter += 1

def main():
    interpreter = Interpreter()
    program = """
PUSH 5
PRINT
ADD
PRINT
SUB
PRINT
MUL
PRINT
DIV
PRINT
DUP
PRINT
SWAP
PRINT
LABEL start
JMP start
"""
    print(interpreter.run(program))


if __name__ == "__main__":
    main()
