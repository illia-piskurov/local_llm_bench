export function solve(input) {
    const { program } = input;
    const lines = program.split('\n').map(line => line.trim());
    const output = [];
    let stack = [];
    let labelJumpTargets = new Map();
    let executionStepCount = 0;
    let lineNum = 1;

    for (const line of lines) {
        if (line.startsWith('#')) continue;
        if (!line) break;

        const parts = line.split(' ');
        const [instruction, ...args] = parts;

        switch (instruction) {
            case 'PUSH':
                stack.push(parseInt(args[0]));
                break;
            case 'POP':
                if (stack.length === 0) return { error: "Stack underflow at line " + lineNum };
                stack.pop();
                break;
            case 'ADD':
                if (stack.length < 2) return { error: "Stack underflow at line " + lineNum };
                const b = stack.pop();
                const a = stack.pop();
                stack.push(a + b);
                break;
            case 'SUB':
                if (stack.length < 2) return { error: "Stack underflow at line " + lineNum };
                const b = stack.pop();
                const a = stack.pop();
                stack.push(a - b);
                break;
            case 'MUL':
                if (stack.length < 2) return { error: "Stack underflow at line " + lineNum };
                const b = stack.pop();
                const a = stack.pop();
                stack.push(a * b);
                break;
            case 'DIV':
                if (stack.length < 2 || args[0] === '0') {
                    return { error: "Division by zero at line " + lineNum };
                }
                const b = parseInt(args[0]);
                const a = stack.pop();
                stack.push(Math.trunc(a / b));
                break;
            case 'DUP':
                if (stack.length === 0) return { error: "Stack underflow at line " + lineNum };
                stack.push(stack[stack.length - 1]);
                break;
            case 'SWAP':
                if (stack.length < 2) return { error: "Stack underflow at line " + lineNum };
                const temp = stack.pop();
                stack.push(stack[stack.length - 1]);
                stack.push(temp);
                break;
            case 'PRINT':
                if (stack.length === 0) return { error: "Stack underflow at line " + lineNum };
                output.push(stack.pop().toString());
                break;
            case 'LABEL':
                labelJumpTargets.set(args[0], executionStepCount);
                break;
            case 'JMP':
                executionStepCount = labelJumpTargets.get(args[0]) || 1001; // Default to max steps if label not found
                break;
            case 'JZ':
                if (stack.length === 0) return { error: "Stack underflow at line " + lineNum };
                if (stack.pop() === 0) executionStepCount = labelJumpTargets.get(args[0]) || 1001; // Default to max steps if label not found
                break;
            case 'JNZ':
                if (stack.length === 0) return { error: "Stack underflow at line " + lineNum };
                if (stack.pop() !== 0) executionStepCount = labelJumpTargets.get(args[0]) || 1001; // Default to max steps if label not found
                break;
            default:
                return { error: `Unknown instruction '${instruction}' at line ${lineNum}` };
        }

        executionStepCount++;
        if (executionStepCount > 1000) {
            return { error: "Execution step limit exceeded" };
        }
    }

    return { output };
}