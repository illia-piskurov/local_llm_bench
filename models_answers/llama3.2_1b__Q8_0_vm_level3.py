def run(program):
    stack = []
    labels = {}
    variables = {}
    for line in program.split('\n'):
        if line.strip().startswith('#'):
            continue
        op, *args = line.split()
        if op == 'PUSH':
            try:
                stack.append(int(args[0]))
                variables[args[0]] = None
            except ValueError:
                raise ValueError(f"Invalid PUSH instruction: {line}")
            labels[args[0]] = len(labels)
        elif op == 'LABEL':
            labels[args[0]] = len(labels)
        elif op == 'CALL':
            if len(stack) < 1:
                raise ValueError(f"Call stack is empty: {line}")
            name = labels[args[0]]
            if name not in variables:
                raise ValueError(f"Variable {name} not defined: {line}")
            variables[name] = stack.pop()
            stack.append(name)
        elif op == 'RET':
            if len(stack) < 1:
                raise ValueError(f"Call stack is empty: {line}")
            name = stack.pop()
            if name not in variables:
                raise ValueError(f"Variable {name} not defined: {line}")
            variables[name] = stack.pop()
        elif op == 'STORE':
            if not variables:
                raise ValueError(f"Variables are empty: {line}")
            var = labels[args[0]]
            if var not in variables:
                raise ValueError(f"Variable {var} not defined: {line}")
            stack.append(variables[var])
            variables[var] = None
        elif op == 'LOAD':
            if not variables:
                raise ValueError(f"Variables are empty: {line}")
            var = labels[args[0]]
            if var not in variables:
                raise ValueError(f"Variable {var} not defined: {line}")
            stack.append(variables[var])
            variables[var] = stack.pop()
        elif op == 'EQ':
            if len(stack) < 2:
                raise ValueError(f"Stack is empty: {line}")
            a, b = stack.pop(), stack.pop()
            stack.append(1 if a == b else 0)
        elif op == 'GT':
            if len(stack) < 2:
                raise ValueError(f"Stack is empty: {line}")
            a, b = stack.pop(), stack.pop()
            stack.append(1 if a > b else 0)
        elif op == 'LT':
            if len(stack) < 2:
                raise ValueError(f"Stack is empty: {line}")
            a, b = stack.pop(), stack.pop()
            stack.append(1 if a < b else 0)
        elif op == 'DUP':
            if len(stack) < 1:
                raise ValueError(f"Stack is empty: {line}")
            stack.append(stack[-1])
        elif op == 'SWAP':
            if len(stack) < 2:
                raise ValueError(f"Stack is empty: {line}")
            a, b = stack.pop(), stack.pop()
            stack.append(a)
            stack.append(b)
        elif op == 'PRINT':
            if not stack:
                raise ValueError(f"Stack is empty: {line}")
            print(stack[-1])
        elif op == 'SUB':
            if len(stack) < 2:
                raise ValueError(f"Stack is empty: {line}")
            a, b = stack.pop(), stack.pop()
            stack.append(a - b)
        elif op == 'ADD':
            if len(stack) < 2:
                raise ValueError(f"Stack is empty: {line}")
            a, b = stack.pop(), stack.pop()
            stack.append(a + b)
        elif op == 'SUBN':
            if len(stack) < 2:
                raise ValueError(f"Stack is empty: {line}")
            a, b = stack.pop(), stack.pop()
            stack.append(a - b)
        elif op == 'MUL':
            if len(stack) < 2:
                raise ValueError(f"Stack is empty: {line}")
            a, b = stack.pop(), stack.pop()
            stack.append(a * b)
        elif op == 'DIV':
            if len(stack) < 2:
                raise ValueError(f"Stack is empty: {line}")
            a, b = stack.pop(), stack.pop()
            if b == 0:
                raise ZeroDivisionError(f"Division by zero: {line}")
            stack.append(a // b)
        elif op == 'JMP':
            if len(stack) < 1:
                raise ValueError(f"Call stack is empty: {line}")
            name = labels[args[0]]
            if name not in variables:
                raise ValueError(f"Variable {name} not defined: {line}")
            variables[name] = stack.pop()
            stack.append(name)
        elif op == 'JZ':
            if len(stack) < 1:
                raise ValueError(f"Call stack is empty: {line}")
            name = labels[args[0]]
            if name not in variables:
                raise ValueError(f"Variable {name} not defined: {line}")
            if stack[-1] == 0:
                stack.pop()
                continue
            raise ZeroDivisionError(f"Division by zero: {line}")
            stack.pop()
        elif op == 'JNZ':
            if len(stack) < 1:
                raise ValueError(f"Call stack is empty: {line}")
            name = labels[args[0]]
            if name not in variables:
                raise ValueError(f"Variable {name} not defined: {line}")
            if stack[-1] != 0:
                stack.pop()
                continue
            raise ZeroDivisionError(f"Division by zero: {line}")
            stack.pop()
        elif op == 'LOAD':
            if not variables:
                raise ValueError(f"Variables are empty: {line}")
            var = labels[args[0]]
            if var not in variables:
                raise ValueError(f"Variable {var} not defined: {line}")
            stack.append(variables[var])
            variables[var] = stack.pop()
        elif op == 'STORE':
            if not variables:
                raise ValueError(f"Variables are empty: {line}")
            var = labels[args[0]]
            if var not in variables:
                raise ValueError(f"Variable {var} not defined: {line}")
            stack.append(variables[var])
            variables[var] = None
        elif op == 'SUB':
            if not variables:
                raise ValueError(f"Variables are empty: {line}")
            var = labels[args[0]]
            if var not in variables:
                raise ValueError(f"Variable {var} not defined: {line}")
            stack.append(variables[var] - 1)
        elif op == 'ADD':
            if not variables:
                raise ValueError(f"Variables are empty: {line}")
            var = labels[args[0]]
            if var not in variables:
                raise ValueError(f"Variable {var} not defined: {line}")
            stack.append(variables[var] + 1)
        elif op == 'SUBN':
            if not variables:
                raise ValueError(f"Variables are empty: {line}")
            var = labels[args[0]]
            if var not in variables:
                raise ValueError(f"Variable {var} not defined: {line}")
            stack.append(variables[var] - 1)
        elif op == 'MUL':
            if not variables:
                raise ValueError(f"Variables are empty: {line}")
            var = labels[args[0]]
            if var not in variables:
                raise ValueError(f"Variable {var} not defined: {line}")
            stack.append(variables[var] * 1)
        elif op == 'DIV':
            if not variables:
                raise ValueError(f"Variables are empty: {line}")
            var = labels[args[0]]
            if var not in variables:
                raise ValueError(f"Variable {var} not defined: {line}")
            if stack[-1] == 0:
                raise ZeroDivisionError(f"Division by zero: {line}")
            stack.append(stack[-1] // var)
        elif op == 'JMP':
            if len(stack) < 1:
                raise ValueError(f"Call stack is empty: {line}")
            name = labels[args[0]]
            if name not in variables:
                raise ValueError(f"Variable {name} not defined: {line}")
            variables[name] = stack.pop()
            stack.append(name)
        elif op == 'JZ':
            if len(stack) < 1:
                raise ValueError(f"Call stack is empty: {line}")
            name = labels[args[0]]
            if name not in variables:
                raise ValueError(f"Variable {name} not defined: {line}")
            if stack[-1] == 0:
                stack.pop()
                continue
            raise ZeroDivisionError(f"Division by zero: {line}")
            stack.pop()
        elif op == 'JNZ':
            if len(stack) < 1:
                raise ValueError(f"Call stack is empty: {line}")
            name = labels[args[0]]
            if name not in variables:
                raise ValueError(f"Variable {name} not defined: {line}")
            if stack[-1] != 0:
                stack.pop()
                continue
            raise ZeroDivisionError(f"Division by zero: {line}")
            stack.pop()
        elif op == 'LOAD':
            if not variables:
                raise ValueError(f"Variables are empty: {line}")
            var = labels[args[0]]
            if var not in variables:
                raise ValueError(f"Variable {var} not defined: {line}")
            stack.append(variables[var])
            variables[var] = stack.pop()
        elif op == 'STORE':
            if not variables:
                raise ValueError(f"Variables are empty: {line}")
            var = labels[args[0]]
            if var not in variables:
                raise ValueError(f"Variable {var} not defined: {line}")
            stack.append(variables[var])
            variables[var] = None
        elif op == 'SUB':
            if not variables:
                raise ValueError(f"Variables are empty: {line}")
            var = labels[args[0]]
            if var not in variables:
                raise ValueError(f"Variable {var} not defined: {line}")
            stack.append(variables[var] - 1)
        elif op == 'ADD':
            if not variables:
                raise ValueError(f"Variables are empty: {line}")
            var = labels[args[0]]
            if var not in variables:
                raise ValueError(f"Variable {var} not defined: {line}")
            stack.append(variables[var] + 1)
        elif op == 'SUBN':
            if not variables:
                raise ValueError(f"Variables are empty: {line}")
            var = labels[args[0]]
            if var not in variables:
                raise ValueError(f"Variable {var} not defined: {line}")
            stack.append(variables[var] - 1)
        elif op == 'MUL':
            if not variables:
                raise ValueError(f"Variables are empty: {line}")
            var = labels[args[0]]
            if var not in variables:
                raise ValueError(f"Variable {var} not defined: {line}")
            stack.append(variables[var] * 1)
        elif op == 'DIV':
            if not variables:
                raise ValueError(f"Variables are empty: {line}")
            var = labels[args[0]]
            if var not in variables:
                raise ValueError(f"Variable {var} not defined: {line}")
            if stack[-1] == 0:
                raise ZeroDivisionError(f"Division by zero: {line}")
            stack.append(stack[-1] // var)
        elif op == 'SUB':
            if not variables:
                raise ValueError(f"Variables are empty: {line}")
            var = labels[args[0]]
            if var not in variables:
                raise ValueError(f"Variable {var} not defined: {line}")
            stack.append(variables[var] - 1)
        elif op == 'ADD':
            if not variables:
                raise ValueError(f"Variables are empty: {line}")
            var = labels[args[0]]
            if var not in variables:
                raise ValueError(f"Variable {var} not defined: {line}")
            stack.append(variables[var] + 1)
        elif op == 'SUBN':
            if not variables:
                raise ValueError(f"Variables are empty: {line}")
            var = labels[args[0]]
            if var not in variables:
                raise ValueError(f"Variable {var} not defined: {line}")
            stack.append(variables[var] - 1)
        elif op == 'MUL':
            if not variables:
                raise ValueError(f"Variables are empty: {line}")
            var = labels[args[0]]
            if var not in variables:
                raise ValueError(f"Variable {var} not defined: {line}")
            stack.append(variables[var] * 1)
        elif op == 'DIV':
            if not variables:
                raise ValueError(f"Variables are empty: {line}")
            var = labels[args[0]]
            if var not in variables:
                raise ValueError(f"Variable {var} not defined: {line}")
            if stack[-1] == 0:
                raise ZeroDivisionError(f"Division by zero: {line}")
            stack.append(stack[-1] // var)
        elif op == 'SUB':
            if not variables:
                raise ValueError(f"Variables are empty: {line}")
            var = labels[args[0]]
            if var not in variables:
                raise ValueError(f"Variable {var} not defined: {line}")
            stack.append(variables[var] - 1)
        elif op == 'ADD':
            if not variables:
                raise ValueError(f"Variables are empty: {line}")
            var = labels[args[0]]
            if var not in variables:
                raise ValueError(f"Variable {var} not defined: {line}")
            stack.append(variables[var] + 1)
        elif op == 'SUBN':
            if not variables:
                raise ValueError(f"Variables are empty: {line}")
            var = labels[args[0]]
            if var not in variables:
                raise ValueError(f"Variable {var} not defined: {line}")
            stack.append(variables[var] - 1)
        elif op == 'MUL':
            if not variables:
                raise ValueError(f"Variables are empty: {line}")
            var = labels[args[0]]
            if var not in variables:
                raise ValueError(f"Variable {var} not defined: {line}")
            stack.append(variables[var] * 1)
        elif op == 'DIV':
            if not variables:
                raise ValueError(f"Variables are empty: {line}")
            var = labels[args[0]]
            if var not in variables:
                raise ValueError(f"Variable {var} not defined: {line}")
            if stack[-1] == 0:
                raise ZeroDivisionError(f"Division by zero: {line}")
            stack.append(stack[-1] // var)
        elif op == 'SUB':
            if not variables:
                raise ValueError(f"Variables are empty: {line}")
            var = labels[args[0]]
            if var not in variables:
                raise ValueError(f"Variable {var} not defined: {line}")
            stack.append(variables[var] - 1)
        elif op == 'ADD':
            if not variables:
                raise ValueError(f"Variables are empty: {line}")
            var = labels[args[0]]
            if var not in variables:
                raise ValueError(f"Variable {var} not defined: {line}")
            stack.append(variables[var] + 1)
        elif op == 'SUBN':
            if not variables:
                raise ValueError(f"Variables are empty: {line}")
            var = labels[args[0]]
            if var not in variables:
                raise ValueError(f"Variable {var} not defined: {line}")
            stack.append(variables[var] - 1)
        elif op == 'MUL':
            if not variables:
                raise ValueError(f"Variables are empty: {line}")
            var = labels[args[0]]
            if var not in variables:
                raise ValueError(f"Variable {var} not defined: {line}")
            stack.append(variables[var] * 1)
        elif op == 'DIV':
            if not variables:
                raise ValueError(f"Variables are empty: {line}")
            var = labels[args[0]]
            if var not in variables:
                raise ValueError(f"Variable {var} not defined: {line}")
            if stack[-1] == 0:
                raise ZeroDivisionError(f"Division by zero: {line}")
            stack.append(stack[-1] // var)
        elif op == 'SUB':
            if not variables:
                raise ValueError(f"Variables are empty: {line}")
            var = labels[args[0]]
            if var not in variables:
                raise ValueError(f"Variable {var} not defined: {line}")
            stack.append(variables[var] - 1)
        elif op == 'ADD':
            if not variables:
                raise ValueError(f"Variables are empty: {line}")
            var = labels[args[0]]
            if var not in variables:
                raise ValueError(f"Variable {var} not defined: {line}")
            stack.append(variables[var] + 1)
        elif op == 'SUBN':
            if not variables:
                raise ValueError(f"Variables are empty: {line}")
            var = labels[args[0]]
            if var not in variables:
                raise ValueError(f"Variable {var} not defined: {line}")
            stack.append(variables[var] - 1)
        elif op == 'MUL':
            if not variables:
                raise ValueError(f"Variables are empty: {line}")
            var = labels[args[0]]
            if var not in variables:
                raise ValueError(f"Variable {var} not defined: {line}")
            stack.append(variables[var] * 1)
        elif op == 'DIV':
            if not variables:
                raise ValueError(f"Variables are empty: {line}")
            var = labels[args[0]]
            if var not in variables:
                raise ValueError(f"Variable {var} not defined: {line}")
            if stack[-1] == 0:
                raise ZeroDivisionError(f"Division by zero: {line}")
            stack.append(stack[-1] // var)
        elif op == 'SUB':
            if not variables:
                raise ValueError(f"Variables are empty: {line}")
            var = labels[args[0]]
            if var not in variables:
                raise ValueError(f"Variable {var} not defined: {line}")
            stack.append(variables[var] - 1)
        elif op == 'ADD':
            if not variables:
                raise ValueError(f"Variables are empty: {line}")
            var = labels[args[0]]
            if var not in variables:
                raise ValueError(f"Variable {var} not defined: {line}")
            stack.append(variables[var] + 1)
        elif op == 'SUBN':
            if not variables:
                raise ValueError(f"Variables are empty: {line}")
            var = labels[args[0]]
            if var not in variables:
                raise ValueError(f"Variable {var} not defined: {line}")
            stack.append(variables[var] - 1)
        elif op == 'MUL':
            if not variables:
                raise ValueError(f"Variables are empty: {line}")
            var = labels[args[0]]
            if var not in variables:
                raise ValueError(f"Variable {var} not defined: {line}")
            stack.append(variables[var] * 1)
        elif op == 'DIV':
            if not variables:
                raise ValueError(f"Variables are empty: {line}")
            var = labels[args[0]]
            if var not in variables:
                raise ValueError(f"Variable {var} not defined: {line}")
            if stack[-1] == 0:
                raise ZeroDivisionError(f"Division by zero: {line}")
            stack.append(stack[-1] // var)
        elif op == 'SUB':
            if not variables:
                raise ValueError(f"Variables are empty: {line}")
            var = labels[args[0]]
            if var not in variables:
                raise ValueError(f"Variable {var} not defined: {line}")
            stack.append(variables[var] - 1)
        elif op == 'ADD':
            if not variables:
                raise ValueError(f"Variables are empty: {line}")
            var = labels[args[0]]
            if var not in variables:
                raise ValueError(f"Variable {var} not defined: {line}")
            stack.append(variables[var] + 1)
        elif op == 'SUBN':
            if not variables:
                raise ValueError(f"Variables are empty: {line}")
            var = labels[args[0]]
            if var not in variables:
                raise ValueError(f"Variable {var} not defined: {line}")
            stack.append(variables[var] - 1)
        elif op == 'MUL':
            if not variables:
                raise ValueError(f"Variables are empty: {line}")
            var = labels[args[0]]
            if var not in variables:
                raise ValueError(f"Variable {var} not defined: {line}")
            stack.append(variables[var] * 1)
        elif op == 'DIV':
            if not variables:
                raise ValueError(f"Variables are empty: {line}")
            var = labels[args[0]]
            if var not in variables:
                raise ValueError(f"Variable {var} not defined: {line}")
            if stack[-1] == 0:
                raise ZeroDivisionError(f"Division by zero: {line}")
            stack.append(stack[-1] // var)
        elif op == 'SUB':
            if not variables:
                raise ValueError(f"Variables are empty: {line}")
            var = labels[args[0]]
            if var not in variables:
                raise ValueError(f"Variable {var} not defined: {line}")
            stack.append(variables[var] - 1)
        elif op == 'ADD':
            if not variables:
                raise ValueError(f"Variables are empty: {line}")
            var = labels[args[0]]
            if var not in variables:
                raise ValueError(f"Variable {var} not defined: {line}")
            stack.append(variables[var] + 1)
        elif op == 'SUBN':
            if not variables:
                raise ValueError(f"Variables are empty: {line}")
            var = labels[args[0]]
            if var not in variables:
                raise ValueError(f"Variable {var} not defined: {line}")
            stack.append(variables[var] - 1)
        elif op == 'MUL':
            if not variables:
                raise ValueError(f"Variables are empty: {line}")
            var = labels[args[0]]
            if var not in variables:
                raise ValueError(f"Variable {var} not defined: {line}")
            stack.append(variables[var] * 1)
        elif op == 'DIV':
            if not variables:
                raise ValueError(f"Variables are empty: {line}")
            var = labels[args[0]]
            if var not in variables:
                raise ValueError(f"Variable {var} not defined: {line}")
            if stack[-1] == 0:
                raise ZeroDivisionError(f"Division by zero: {line}")
            stack.append(stack[-1] // var)
        elif op == 'SUB':
            if not variables:
                raise ValueError(f"Variables are empty: {line}")
            var = labels[args[0]]
            if var not in variables:
                raise ValueError(f"Variable {var} not defined: {line}")
            stack.append(variables[var] - 1)
        elif op == 'ADD':
            if not variables:
                raise ValueError(f"Variables are empty: {line}")
            var = labels[args[0]]
            if var not in variables:
                raise ValueError(f"Variable {var} not defined: {line}")
            stack.append(variables[var] + 1)
        elif op == 'SUBN':
            if not variables:
                raise ValueError(f"Variables are empty: {line}")
            var = labels[args[0]]
            if var not in variables:
                raise ValueError(f"Variable {var} not defined: {line}")
            stack.append(variables[var] - 1)
        elif op == 'MUL':
            if not variables:
                raise ValueError(f"Variables are empty: {line}")
            var = labels[args[0]]
            if var not in variables:
                raise ValueError(f"Variable {var} not defined: {line}")
            stack.append(variables[var] * 1)
        elif op == 'DIV':
            if not variables:
                raise ValueError(f"Variables are empty: {line}")
            var = labels[args[0]]
            if var not in variables:
                raise ValueError(f"Variable {var} not defined: {line}")
            if stack[-1] == 0:
                raise ZeroDivisionError(f"Division by zero: {line}")
            stack.append(stack[-1] // var)
        elif op == 'SUB':
            if not variables:
                raise ValueError(f"Variables are empty: {line}")
            var = labels[args[0]]
            if var not in variables:
                raise ValueError(f"Variable {var} not defined: {line}")
            stack.append(variables[var] - 1)
        elif op == 'ADD':
            if not variables:
                raise ValueError(f"Variables are empty: {line}")
            var = labels[args[0]]
            if var not in variables:
                raise ValueError(f"Variable {var} not defined: {line}")
            stack.append(variables[var] + 1)
        elif op == 'SUBN':
            if not variables:
                raise ValueError(f"Variables are empty: {line}")
            var = labels[args[0]]
            if var not in variables:
                raise ValueError(f"Variable {var} not defined: {line}")
            stack.append(variables[var] - 1)
        elif op == 'MUL':
            if not variables:
                raise ValueError(f"Variables are empty: {line}")
            var = labels[args[0]]
            if var not in variables:
                raise ValueError(f"Variable {var} not defined: {line}")
            stack.append(variables[var] * 1)
        elif op == 'DIV':
            if not variables:
                raise ValueError(f"Variables are empty: {line}")
            var = labels[args[0]]
            if var not in variables:
                raise ValueError(f"Variable {var} not defined: {line}")
            if stack[-1] == 0:
                raise ZeroDivisionError(f"Division by zero: {line}")
            stack.append(stack[-1] // var)
        elif op == 'SUB':
            if not variables:
                raise ValueError(f"Variables are empty: {line}")
            var = labels[args[0]]
            if var not in variables:
                raise ValueError(f"Variable {var} not defined: {line}")
            stack.append(variables[var] - 1)
        elif op == 'ADD':
            if not variables:
                raise ValueError(f"Variables are empty: {line}")
            var = labels[args[0]]
            if var not in variables:
                raise ValueError(f"Variable {var} not defined: {line}")
            stack.append(variables[var] + 1)
        elif op == 'SUBN':
            if not variables:
                raise ValueError(f"Variables are empty: {line}")
            var = labels[args[0]]
            if var not in variables:
                raise ValueError(f"Variable {var} not defined: {line}")
            stack.append(variables[var] - 1)
        elif op == 'MUL':
            if not variables:
                raise ValueError(f"Variables are empty: {line}")
            var = labels[args[0]]
            if var not in variables:
                raise ValueError(f"Variable {var} not defined: {line}")
            stack.append(variables[var] * 1)
        elif op == 'DIV':
            if not variables:
                raise ValueError(f"Variables are empty: {line}")
            var = labels[args[0]]
            if var not in variables:
                raise ValueError(f"Variable {var} not defined: {line}")
            if stack[-1] == 0:
                raise ZeroDivisionError(f"Division by zero: {line}")
            stack.append(stack[-1] // var)
        elif op == 'SUB':
            if not variables:
                raise ValueError(f"Variables are empty: {line}")
            var = labels[args[0]]
            if var not in variables:
                raise ValueError(f"Variable {var} not defined: {line}")
            stack.append(variables[var] - 1)
        elif op == 'ADD':
            if not variables:
                raise ValueError(f"Variables are empty: {line}")
            var = labels[args[0]]
            if var not in variables:
                raise ValueError(f"Variable {var} not defined: {line}")
            stack.append(variables[var] + 1)
        elif op == 'SUBN':
            if not variables:
                raise ValueError(f"Variables are empty: {line}")
            var = labels[args[0]]
            if var not in variables:
                raise ValueError(f"Variable {var} not defined: {line}")
            stack.append(variables[var] - 1)
        elif op == 'MUL':
            if not variables:
                raise ValueError(f"Variables are empty: {line}")
            var = labels[args[0]]
            if var not in variables:
                raise ValueError(f"Variable {var} not defined: {line}")
            stack.append(variables[var] * 1)
        elif op == 'DIV':
            if not variables:
                raise ValueError(f"Variables are empty: {line}")
            var = labels[args[0]]
            if var not in variables:
                raise ValueError(f"Variable {var} not defined: {line}")
            if stack[-1] == 0:
                raise ZeroDivisionError(f"Division by zero: {line}")
            stack.append(stack[-1] // var)
        elif op == 'SUB':
            if not variables:
                raise ValueError(f"Variables are empty: {line}")
            var = labels[args[0]]
            if var not in variables:
                raise ValueError(f"Variable {var} not defined: {line}")
            stack.append(variables[var] - 1)
        elif op == 'ADD':
            if not variables:
                raise ValueError(f"Variables are empty: {line}")
            var = labels[args[0]]
            if var not in variables:
                raise ValueError(f"Variable {var} not defined: {line}")
            stack.append(variables[var] + 1)
        elif op == 'SUBN':
            if not variables:
                raise ValueError(f"Variables are empty: {line}")
            var = labels[args[0]]
            if var not in variables:
                raise ValueError(f"Variable {var} not defined: {line}")
            stack.append(variables[var] - 1)
        elif op == 'MUL':
            if not variables:
                raise ValueError(f"Variables are empty: {line}")
            var = labels[args[0]]
            if var not in variables:
                raise ValueError(f"Variable {var} not defined: {line}")
            stack.append(variables[var] * 1)
        elif op == 'DIV':
            if not variables:
                raise ValueError(f"Variables are empty: {line}")
            var = labels[args[0]]
            if var not in variables:
                raise ValueError(f"Variable {var} not defined: {line}")
            if stack[-1] == 0:
                raise ZeroDivisionError(f"Division by zero: {line}")
            stack.append(stack[-1] // var)
        elif op == 'SUB':
            if not variables:
                raise ValueError(f"Variables are empty: {line}")
            var = labels[args[0]]
            if var not in variables:
                raise ValueError(f"Variable {var} not defined: {line}")
            stack.append(variables[var] - 1)
        elif op == 'ADD':
            if not variables:
                raise ValueError(f"Variables are empty: {line}")
            var = labels[args[0]]
            if var not in variables:
                raise ValueError(f"Variable {var} not defined: {line}")
            stack.append(variables[var] + 1)
        elif op == 'SUBN':
            if not variables:
                raise ValueError(f"Variables are empty: {line}")
            var = labels[args[0]]
            if var not in variables:
                raise ValueError(f"Variable {var} not defined: {line}")
            stack.append(variables[var] - 1)
        elif op == 'MUL':
            if not variables:
                raise ValueError(f"Variables are empty: {line}")
            var = labels[args[0]]
            if var not in variables:
                raise ValueError(f"Variable {var} not defined: {line}")
            stack.append(variables[var] * 1)
        elif op == 'DIV':
            if not variables:
                raise ValueError(f"Variables are empty: {line}")
            var = labels[args[0]]
            if var not in variables:
                raise ValueError(f"Variable {var} not defined: {line}")
            if stack[-1] == 0:
                raise ZeroDivisionError(f"Division by zero: {line}")
            stack.append(stack[-1] // var)
        elif op == 'SUB':
            if not variables:
                raise ValueError(f"Variables are empty: {line}")
            var = labels[args[0]]
            if var not in variables:
                raise ValueError(f"Variable {var} not defined: {line}")
            stack.append(variables[var] - 1)
        elif op == 'ADD':
            if not variables:
                raise ValueError(f"Variables are empty: {line}")
            var = labels[args[0]]
            if var not in variables:
                raise ValueError(f"Variable {var} not defined: {line}")
            stack.append(variables[var] + 1)
        elif op == 'SUBN':
            if not variables:
                raise ValueError(f"Variables are empty: {line}")
            var = labels[args[0]]
            if var not in variables:
                raise ValueError(f"Variable {var} not defined: {line}")
            stack.append(variables[var] - 1)
        elif op == 'MUL':
            if not variables:
                raise ValueError(f"Variables are empty: {line}")
            var = labels[args[0]]
            if var not in variables:
                raise ValueError(f"Variable {var} not defined: {line}")
            stack.append(variables[var] * 1)
        elif op == 'DIV':
            if not variables:
                raise ValueError(f"Variables are empty: {line}")
            var = labels[args[0]]
            if var not in variables:
                raise ValueError(f"Variable {var} not defined: {line}")
            if stack[-1] == 0:
                raise ZeroDivisionError(f"Division by zero: {line}")
            stack.append(stack[-1] // var)
        elif op == 'SUB':
            if not variables:
                raise ValueError(f"Variables are empty: {line}")
            var = labels[args[0]]
            if var not in variables:
                raise ValueError(f"Variable {var} not defined: {line}")
            stack.append(variables[var] - 1)
        elif op == 'ADD':
            if not variables:
                raise ValueError(f"Variables are empty: {line}")
            var = labels[args[0]]
            if var not in variables:
                raise ValueError(f"Variable {var} not defined: {line}")
            stack.append(variables[var] + 1)
        elif op == 'SUBN':
            if not variables:
                raise ValueError(f"Variables are empty: {line}")
            var = labels[args[0]]
            if var not in variables:
                raise ValueError(f"Variable {var} not defined: {line}")
            stack.append(variables[var] - 1)
        elif op == 'MUL':
            if not variables:
                raise ValueError(f"Variables are empty: {line}")
            var = labels[args[0]]
            if var not in variables:
                raise ValueError(f"Variable {var} not defined: {line}")
            stack.append(variables[var] * 1)
        elif op == 'DIV':
            if not variables:
                raise ValueError(f"Variables are empty: {line}")
            var = labels[args[0]]
            if var not in variables:
                raise ValueError(f"Variable {var} not defined: {line}")
            if stack[-1] == 0:
                raise ZeroDivisionError(f"Division by zero: {line}")
            stack.append(stack[-1] // var)
        elif op == 'SUB':
            if not variables:
                raise ValueError(f"Variables are empty: {line}")
            var = labels[args[0]]
            if var not in variables:
                raise ValueError(f"Variable {var} not defined: {line}")
            stack.append(variables[var] - 1)
        elif op == 'ADD':
            if not variables:
                raise ValueError(f"Variables are empty: {line}")
            var = labels[args[0]]
            if var not in variables:
                raise ValueError(f"Variable {var} not defined: {line}")
            stack.append(variables[var] + 1)
        elif op == 'SUBN':
            if not variables:
                raise ValueError(f"Variables are empty: {line}")
            var = labels[args[0]]
            if var not in variables:
                raise ValueError(f"Variable {var} not defined: {line}")
            stack.append(variables[var] - 1)
        elif op == 'MUL':
            if not variables:
                raise ValueError(f"Variables are empty: {line}")
            var = labels[args[0]]
            if var not in variables:
                raise ValueError(f"Variable {var} not defined: {line}")
            stack.append(variables[var] * 1)
        elif op == 'DIV':
            if not variables:
                raise ValueError(f"Variables are empty: {line}")
            var = labels[args[0]]
            if var not in variables:
                raise ValueError(f"Variable {var} not defined: {line}")
            if stack[-1] == 0:
                raise ZeroDivisionError(f"Division by zero: {line}")
            stack.append(stack[-1] // var)
        elif op == 'SUB':
            if not variables:
                raise ValueError(f"Variables are empty: {line}")
            var = labels[args[0]]
            if var not in variables:
                raise ValueError(f"Variable {var} not defined: {line}")
            stack.append(variables[var] - 1)
        elif op == 'ADD':
            if not variables:
                raise ValueError(f"Variables are empty: {line}")
            var = labels[args[0]]
            if var not in variables:
                raise ValueError(f"Variable {var} not defined: {line}")
            stack.append(variables[var] + 1)
        elif op == 'SUBN':
            if not variables:
                raise ValueError(f"Variables are empty: {line}")
            var = labels[args[0]]
            if var not in variables:
                raise ValueError(f"Variable {var} not defined: {line}")
            stack.append(variables[var] - 1)
    return stack
