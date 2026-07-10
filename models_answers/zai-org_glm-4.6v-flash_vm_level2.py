def run(program: str) -> list[str]:
    labels = {}
    stack = []
    output_lines = []

    lines = program.strip().split('\n')
    
    i = 0  # current line index (0-based for internal loop)
    while True:
        if i >= len(lines):
            break

        line = lines[i].strip()
        
        # Skip empty or comment lines
        if not line or line.startswith('#'):
            i += 1
            continue
            
        parts = line.split()
        cmd = parts[0].upper()

        try:
            if cmd == 'PUSH':
                if len(parts) != 2:
                    raise ValueError(f"Expected number after PUSH, got {parts}")
                num = int(parts[1])
                stack.append(num)
                
            elif cmd == 'POP':
                if not stack:
                    raise IndexError(f"Stack underflow at line {i+1}")
                stack.pop()
                
            elif cmd == 'ADD':
                if len(stack) < 2:
                    raise IndexError(f"Not enough operands for ADD at line {i+1}")
                b = stack.pop()
                a = stack.pop()
                stack.append(a + b)
                
            elif cmd == 'SUB':
                if len(stack) < 2:
                    raise IndexError(f"Not enough operands for SUB at line {i+1}")
                b = stack.pop()   # first popped is b
                a = stack.pop()   # then a
                stack.append(a - b)
                
            elif cmd == 'MUL':
                if len(stack) < 2:
                    raise IndexError(f"Not enough operands for MUL at line {i+1}")
                b = stack.pop()
                a = stack.pop()
                stack.append(a * b)
                
            elif cmd == 'DIV':
                if len(stack) < 2:
                    raise IndexError(f"Not enough operands for DIV at line {i+1}")
                b = stack.pop()
                a = stack.pop()
                if b == 0:
                    raise ZeroDivisionError(f"Divide by zero at line {i+1}")
                stack.append(a // b)
                
            elif cmd == 'DUP':
                if not stack:
                    raise IndexError(f"Stack underflow for DUP at line {i+1}")
                stack.append(stack[-1])
                
            elif cmd == 'SWAP':
                if len(stack) < 2:
                    raise IndexError(f"Not enough operands for SWAP at line {i+1}")
                b = stack.pop()
                a = stack.pop()
                stack.append(b)
                stack.append(a)
                
            elif cmd == 'PRINT':
                if not stack:
                    raise IndexError(f"Stack underflow for PRINT at line {i+1}")
                output_lines.append(str(stack[-1]))
                
            elif cmd == 'LABEL':
                label_name = parts[1]
                if label_name in labels:
                    raise ValueError(f"Label '{label_name}' already defined at line {i+1}")
                labels[label_name] = i  # store the current (0-based) index
                
            elif cmd == 'JMP':
                target_label = parts[1]
                if target_label not in labels:
                    raise ValueError(f"Unknown label '{target_label}' at line {i+1}")
                i = labels[target_label] - 1  # jump to that line, so we increment i later
                continue
                
            elif cmd == 'JZ':
                if not stack:
                    raise IndexError(f"Stack underflow for JZ at line {i+1}")
                value = stack.pop()
                target_label = parts[1]
                if target_label not in labels:
                    raise ValueError(f"Unknown label '{target_label}' at line {i+1}")
                if value == 0:
                    i = labels[target_label] - 1
                    continue
                    
            elif cmd == 'JNZ':
                if not stack:
                    raise IndexError(f"Stack underflow for JNZ at line {i+1}")
                value = stack.pop()
                target_label = parts[1]
                if target_label not in labels:
                    raise ValueError(f"Unknown label '{target_label}' at line {i+1}")
                if value != 0:
                    i = labels[target_label] - 1
                    continue
                    
            else:
                # This should handle existing commands, but we can just let the default case fail.
                pass
                
        except Exception as e:
            raise RuntimeError(f"Error at line {i+1}: {str(e)}")

        i += 1

    return output_lines


if __name__ == "__main__":
    sample_program = """PUSH 5
PUSH 3
ADD
PRINT

PUSH 10
PUSH 0
DIV
"""
    print(run(sample_program))
