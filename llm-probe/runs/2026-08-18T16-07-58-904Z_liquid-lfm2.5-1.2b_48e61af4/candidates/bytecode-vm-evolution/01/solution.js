export function solve(input) {
    const lines = input.program.split('\n');
    const stack = [];
    let error = '';
    let lineNum = 1;
    const maxSteps = 1000;
    const output = [];
    let i = 0;

    while (i < lines.length && lineNum <= maxSteps) {
        const line = lines[lineNum];
        lineNum++;

        // Skip comments and empty lines
        if (line.startsWith('#') || line.trim() === '') continue;

        if (line === 'LABEL <name>') {
            // No-op for execution
            i++;
            continue;
        }

        if (line.startsWith('JMP')) {
            const jumpName = line.slice(4);
            i++;
            continue;
        }

        if (line.startsWith('JZ')) {
            const val = parseInt(line.slice(4));
            if (val === 0) {
                error = `Division by zero at line ${lineNum}`;
                break;
            }
            i++;
            continue;
        }

        if (line.startsWith('JNZ')) {
            const val = parseInt(line.slice(4));
            i++;
            continue;
        }

        // PUSH
        if (line.startsWith('PUSH')) {
            const parts = line.split(' ');
            if (parts.length !== 2) {
                error = `Invalid PUSH instruction at line ${lineNum}`;
                break;
            }
            const arg = parseInt(parts[1]);
            stack.push(arg);
        } else if (line.startsWith('PRINT')) {
            output.push(stack.pop() ?? '');
        } else if (line.startsWith('SWAP')) {
            [stack[stack.length - 1], stack[stack.length - 2]] = [stack[stack.length - 2], stack[stack.length - 1]];
        } else if (line.startsWith('DUP')) {
            stack.push(stack[stack.length - 1]);
        } else if (line.startsWith('ADD')) {
            if (stack.length < 2) error = `Stack underflow at line ${lineNum}`;
            const b = stack.pop();
            const a = stack.pop();
            stack.push(a + b);
        } else if (line.startsWith('SUB')) {
            if (stack.length < 2) error = `Stack underflow at line ${lineNum}`;
            const b = stack.pop();
            const a = stack.pop();
            stack.push(a - b);
        } else if (line.startsWith('MUL')) {
            if (stack.length < 2) error = `Stack underflow at line ${lineNum}`;
            const b = stack.pop();
            const a = stack.pop();
            stack.push(a * b);
        } else if (line.startsWith('DIV')) {
            if (stack.length < 2) error = `Stack underflow at line ${lineNum}`;
            const b = stack.pop();
            const a = stack.pop();
            if (b === 0) error = `Division by zero at line ${lineNum}`;
            else stack.push(Math.trunc(a / b));
        } else if (line.startsWith('POP')) {
            if (stack.length < 1) error = `Stack underflow at line ${lineNum}`;
            const val = stack.pop();
            output.push(val);
        } else if (line.startsWith('LABEL')) {
            i++;
            continue;
        } else if (line.startsWith('PRINT')) {
            // Only push if not popping
            if (stack.length > 0) output.push(stack.pop());
        } else if (line.startsWith('INVALID')) {
            error = `Unknown instruction "${line.slice(1)}" at line ${lineNum}`;
            break;
        }

        // Check step limit
        if (i >= maxSteps) error = 'Execution step limit exceeded';
    }

    return { output, error };
}