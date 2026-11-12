def run(program: str) -> list[str]:
    # Parse and execute instructions, supporting subroutines, comparisons, and named variables
    instructions = []
    stack = []  # call stack
    variables = {}  # named variables

    for line in program.split():
        # Call subroutine
        if line.startswith('CALL'):
            name = line.split(' ')[1]
            stack.append(return_address)
            instructions.append(f"CALL {name}")
            instructions.append(f"JMP {name}")
        # Jump unconditional
        elif line.startswith('JMP'):
            name = line.split(' ')[1]
            instructions.append(f"JMP {name}")
        # Conditional jump (JZ)
        elif line.startswith('JZ'):
            name = line.split(' ')[1]
            if not stack:
                raise ValueError("Empty stack for JZ")
            value = pop_value()
            instructions.append(f"JZ {name}")
            instructions.append(f"pop {value}")
        # Conditional jump (JNZ)
        elif line.startswith('JNZ'):
            name = line.split(' ')[1]
            if not stack:
                raise ValueError("Empty stack for JNZ")
            value = pop_value()
            instructions.append(f"JNZ {name}")
            instructions.append(f"pop {value}")
        # Comparison operations
        elif line.startswith('EQ'):
            b, a = pop_values()
            instructions.append(f"EQ {b}, {a}")
        elif line.startswith('GT'):
            b, a = pop_values()
            instructions.append(f"GT {b}, {a}")
        elif line.startswith('LT'):
            b, a = pop_values()
            instructions.append(f"LT {b}, {a}")
        # Store variable
        elif line.startswith('STORE'):
            var = line.split(' ')[1]
            value = pop_value()
            instructions.append(f"STORE {var}")
            instructions.append(f"pop {value}")
        # Load variable
        elif line.startswith('LOAD'):
            var = line.split(' ')[1]
            if var not in variables:
                raise ValueError(f"Variable {var} not stored yet")
            value = load_variable(var)
            instructions.append(f"LOAD {var}")
            instructions.append(f"push {value}")
    # After processing, ensure return address is on stack
    if not stack:
        raise ValueError("Call stack is empty")
    return instructions
