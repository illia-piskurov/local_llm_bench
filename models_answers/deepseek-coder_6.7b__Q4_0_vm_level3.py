class StackMachine:
    def __init__(self):
        self.stack = []
        self.labels = {}
        self.variables = {}
        self.call_stack = []
        self.commands = {
            'PUSH': self.push,
            'POP': self.pop,
            'ADD': self.add,
            'SUB': self.sub,
            'MUL': self.mul,
            'DIV': self.div,
            'DUP': self.dup,
            'SWAP': self.swap,
            'PRINT': self.print_top,
            'LABEL': self.label,
            'JMP': self.jmp,
            'JZ': self.jz,
            'JNZ': self.jnz,
            'CALL': self.call,
            'RET': self.ret,
            'EQ': self.eq,
            'GT': self.gt,
            'LT': self.lt,
            'STORE': self.store,
            'LOAD': self.load
        }
        self.output = []

    def push(self, value):
        self.stack.append(int(value))

    def pop(self):
        return self.stack.pop()

    def add(self):
        self.stack.append(self.stack.pop() + self.stack.pop())

    def sub(self):
        b = self.stack.pop()
        a = self.stack.pop()
        self.stack.append(a - b)

    def mul(self):
        self.stack.append(self.stack.pop() * self.stack.pop())

    def div(self):
        b = self.stack.pop()
        a = self.stack.pop()
        if b == 0:
            raise Exception('Division by zero')
        self.stack.append(a // b)

    def dup(self):
        self.stack.append(self.stack[-1])

    def swap(self):
        a = self.stack.pop()
        b = self.stack.pop()
        self.stack.append(a)
        self.stack.append(b)

    def print_top(self):
        self.output.append(str(self.stack[-1]))

    def label(self, name):
        self.labels[name] = len(self.output)

    def jmp(self, name):
        self.pc = self.labels[name]

    def jz(self, name):
        if self.stack.pop() == 0:
            self.pc = self.labels[name]

    def jnz(self, name):
        if self.stack[-1] != 0:
            self.pc = self.labels[name]

    def call(self, name):
        self.call_stack.append(self.pc)
        self.pc = self.labels[name]

    def ret(self):
        if not self.call_stack:
            raise Exception('Empty call stack')
        self.pc = self.call_stack.pop()

    def eq(self):
        b = self.stack.pop()
        a = self.stack.pop()
        self.stack.append(1 if a == b else 0)

    def gt(self):
        b = self.stack.pop()
        a = self.stack.pop()
        self.stack.append(1 if a > b else 0)

    def lt(self):
        b = self.stack.pop()
        a = self.stack.pop()
        self.stack.append(1 if a < b else 0)

    def store(self, var):
        self.variables[var] = self.stack.pop()

    def load(self, var):
        if var not in self.variables:
            raise Exception('Variable not found')
        self.stack.append(self.variables[var])

    def run(self, program):
        lines = program.split('\n')
        for line_num, line in enumerate(lines, start=1):
            if line and not line.startswith('#'):
                instruction, *args = line.split()
                command = self.commands.get(instruction)
                if command:
                    if args:
                        command(*args)
                    else:
                        command()
                else:
                    raise Exception('Unknown instruction at line {}'.format(line_num))
        return self.output

machine = StackMachine()
