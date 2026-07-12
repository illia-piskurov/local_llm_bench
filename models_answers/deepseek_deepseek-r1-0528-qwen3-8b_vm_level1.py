class StackInterpreter:
    def __init__(self):
        self.stack = []
        self.output_lines = []

    def push(self, n):
        try:
            num = int(n)
        except ValueError:
            raise Exception("Invalid integer argument for PUSH")
        self.stack.append(num)

    def pop(self):
        if not self.stack:
            raise Exception(f"Error at line {self.line_num}: Stack is empty. Cannot POP.")
        return self.stack.pop()

    def add(self):
        if len(self.stack) < 2:
            raise Exception(f"Error at line {self.line_num}: Not enough elements for ADD operation (need two).")
        a = self.pop()
        b = self.pop()
        result = a + b
        self.stack.append(result)

    def sub(self):
        if len(self.stack) < 2:
            raise Exception(f"Error at line {self.line_num}: Not enough elements for SUB operation (need two).")
        b = self.pop()
        a = self.pop()
        result = a - b
        self.stack.append(result)

    def mul(self):
        if len(self.stack) < 2:
            raise Exception(f"Error at line {self.line_num}: Not enough elements for MUL operation (need two).")
        a = self.pop()
        b = self.pop()
        result = a * b
        self.stack.append(result)

    def div(self):
        if len(self.stack) < 2:
            raise Exception(f"Error at line {self.line_num}: Not enough elements for DIV operation (need two).")
        try:
            b = self.pop()
            a = self.pop()
            result = int(a / b)
        except ZeroDivisionError:
            raise Exception("Division by zero is not allowed.")
        self.stack.append(result)

    def dup(self):
        if len(self.stack) < 1:
            raise Exception(f"Error at line {self.line_num}: Stack is empty. Cannot DUP.")
        value = self.stack[-1]
        self.stack.append(value)

    def swap(self):
        if len(self.stack) < 2:
            raise Exception(f"Error at line {self.line_num}: Not enough elements for SWAP operation (need two).")
        a = self.pop()
        b = self.pop()
        self.stack.append(a)
        self.stack.append(b)

    def print_top(self):
        if not self.stack:
            raise Exception(f"Error at line {self.line_num}: Stack is empty. Cannot PRINT.")
        value = self.stack[-1]
        output_line = f"{value}"
        self.output_lines.append(output_line)
        return output_line

    def process_line(self, line, line_num):
        stripped_line = line.strip()
        if not stripped_line:
            return
        if stripped_line.startswith('#'):
            return
        parts = stripped_line.split()
        command = parts[0].upper()
        args = parts[1:] if len(parts) > 1 else []

        try:
            getattr(self, command)(*(args or [None]))
        except Exception as e:
            raise Exception(f"Error at line {line_num}: {str(e)}")

    def run(self, program):
        self.output_lines.clear()
        lines = program.splitlines()
        for i in range(len(lines)):
            if not lines[i].strip().startswith('#'):
                self.line_num = i + 1
                try:
                    self.process_line(lines[i], self.line_num)
                except Exception as e:
                    # If error occurs, we still want to return the collected output_lines so far.
                    pass

        return self.output_lines


def main():
    import sys
    if len(sys.argv) < 2:
        print("Usage: python stack_interpreter.py <program>")
        sys.exit(1)

    program = sys.argv[1]
    interpreter = StackInterpreter()
    try:
        output = interpreter.run(program)
        for line in output:
            print(line, end='')
        print()  # Ensure newline after last printed value
    except Exception as e:
        error_msg = str(e).split(": ")[-1] if isinstance(e, Exception) else "Unknown error"
        print(f"Error: {error_msg}")

if __name__ == "__main__":
    main()
