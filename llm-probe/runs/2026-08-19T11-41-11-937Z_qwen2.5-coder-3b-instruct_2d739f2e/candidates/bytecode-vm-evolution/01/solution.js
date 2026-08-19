export function solve(input) {
    const lines = input.program.split('\n');
    const output = [];
    let stack = [];
    let lineNum = 0;
    let executionStep = 0;

    while (lineNum < lines.length && executionStep < 1000) {
        lineNum++;
        const [instruction, ...args] = lines[lineNum - 1].trim().split(' ');

        if (!instruction || instruction.startsWith('#')) continue; // Skip empty and comment lines

        switch (instruction) {
            case 'PUSH':
                if (args.length === 0) return { output, error: `Stack underflow at line ${lineNum}` };
                stack.push(Number(args[0]));
                break;
            case 'POP':
                if (stack.length === 0) return { output, error: `Stack underflow at line ${lineNum}` };
                stack.pop();
                break;
            case 'ADD':
                if (stack.length < 2) return { output, error: `Stack underflow at line ${lineNum}` };
                const b = stack.pop();
                const a = stack.pop();
                stack.push(a + b);
                break;
            case 'SUB':
                if (stack.length < 2) return { output, error: `Stack underflow at line ${lineNum}` };
                const b = stack.pop();
                const a = stack.pop();
                stack.push(a - b);
                break;
            case 'MUL':
                if (stack.length < 2) return { output, error: `Stack underflow at line ${lineNum}` };
                const b = stack.pop();
                const a = stack.pop();
                stack.push(a * b);
                break;
            case 'DIV':
                if (stack.length < 2) return { output, error: `Stack underflow at line ${lineNum}` };
                const b = stack.pop();
                const a = stack.pop();
                if (b === 0) return { output, error: `Division by zero at line ${lineNum}` };
                stack.push(Math.trunc(a / b));
                break;
            case 'DUP':
                if (stack.length === 0) return { output, error: `Stack underflow at line ${lineNum}` };
                const value = stack[stack.length - 1];
                stack.push(value);
                break;
            case 'SWAP':
                if (stack.length < 2) return { output, error: `Stack underflow at line ${lineNum}` };
                [stack[stack.length - 2], stack[stack.length - 1]] = [stack[stack.length - 1], stack[stack.length - 2]];
                break;
            case 'PRINT':
                if (stack.length === 0) return { output, error: `Stack underflow at line ${lineNum}` };
                output.push(stack.pop().toString());
                break;
            case 'LABEL':
                // Labels are just defined as comments for now
                continue;
            case 'JMP':
                const labelName = args[0];
                let found = false;
                for (let i = lineNum; i < lines.length; i++) {
                    if (lines[i].trim().startsWith(`LABEL ${labelName}`)) {
                        found = true;
                        lineNum = i + 1;
                        break;
                    }
                }
                if (!found) return { output, error: `Unknown label '${labelName}' at line ${lineNum}` };
                break;
            case 'JZ':
                const jzLabelName = args[0];
                let value = stack.pop();
                if (value === 0) {
                    let found = false;
                    for (let i = lineNum; i < lines.length; i++) {
                        if (lines[i].trim().startsWith(`LABEL ${jzLabelName}`)) {
                            found = true;
                            lineNum = i + 1;
                            break;
                        }
                    }
                    if (!found) return { output, error: `Unknown label '${jzLabelName}' at line ${lineNum}` };
                } else {
                    lineNum--;
                }
                break;
            case 'JNZ':
                const jnzLabelName = args[0];
                let value = stack.pop();
                if (value !== 0) {
                    let found = false;
                    for (let i = lineNum; i < lines.length; i++) {
                        if (lines[i].trim().startsWith(`LABEL ${jnzLabelName}`)) {
                            found = true;
                            lineNum = i + 1;
                            break;
                        }
                    }
                    if (!found) return { output, error: `Unknown label '${jnzLabelName}' at line ${lineNum}` };
                } else {
                    lineNum--;
                }
                break;
            default:
                return { output, error: `Unknown instruction '${instruction}' at line ${lineNum}` };
        }

        executionStep++;
    }

    if (executionStep >= 1000) {
        return { output, error: "Execution step limit exceeded" };
    }

    return { output };
}