class Stack:
    def  __init__(self):
        self.items = []

    # ... existing code ...

    def label(self, name):
        self.labels[name] = len(self.items)

    def jmp(self, name):
        pos = self.labels.get(name, None)
        if pos is None:
            raise ValueError(f"Label {name} not found")
        self.ip = pos

    def jz(self, name):
        pos = self.labels.get(name, None)
        if pos is None:
            raise ValueError(f"Label {name} not found")
        if self.items[self.sp] == 0:
            self.ip = pos

    def jnz(self, name):
        pos = self.labels.get(name, None)
        if pos is None:
            raise ValueError(f"Label {name} not found")
        if self.items[self.sp] != 0:
            self.ip = pos


def run(program):
    lines = program.split('\n')
    stack = Stack()
    printed = []

    for line_num, line in enumerate(lines, start=1):
        line = line.strip()
        if line:
            if line.startswith('PUSH'):
                stack.push(int(line[4:]))
            elif line == 'PRINT':
                stack.print()
                printed.append(str(stack.items[-1]))
            elif line == 'DIV':
                stack.div()
            elif line == 'SUB':
                stack.sub()
            elif line == 'MUL':
                stack.mul()
            elif line == 'ADD':
                stack.add()
            elif line == 'DUP':
                stack.dup()
            elif line == 'SWAP':
                stack.swap()
            elif line.startswith('LABEL'):
                stack.label(line[7:])
            elif line == 'JMP':
                stack.jmp(line[4:])
            elif line == 'JZ':
                stack.jz(line[4:])
            elif line == 'JNZ':
                stack.jnz(line[4:])
            else:
                raise ValueError(f"Invalid instruction at line  {line_num}")

    return printed
