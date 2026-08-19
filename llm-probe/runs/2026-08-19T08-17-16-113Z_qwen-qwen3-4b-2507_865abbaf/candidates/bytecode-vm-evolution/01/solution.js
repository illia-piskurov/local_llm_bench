export function solve(input) {
    const program = input.program;
    const lines = program.split('\n').map(line => line.trim());
    const instructions = [];
    const lineNumbers = [];
    
    let currentLine = 0;
    let stack = [];
    let output = [];
    let stepCount = 0;
    let labels = {};
    
    // Parse lines and extract instructions
    for (let i = 0; i < lines.length; i++) {
        const line = lines[i];
        if (!line || line.startsWith('#')) {
            lineNumbers.push(0);
            continue;
        }
        
        lineNumbers.push(i + 1);
        
        const parts = line.split(' ');
        const instruction = parts[0];
        
        if (instruction === 'PUSH') {
            const value = parseInt(parts[1]);
            if (isNaN(value)) {
                throw new Error(`Invalid integer in PUSH at line ${i + 1}`);
            }
            instructions.push(['PUSH', value]);
        } else if (instruction === 'POP') {
            instructions.push(['POP']);
        } else if (instruction === 'ADD') {
            instructions.push(['ADD']);
        } else if (instruction === 'SUB') {
            instructions.push(['SUB']);
        } else if (instruction === 'MUL') {
            instructions.push(['MUL']);
        } else if (instruction === 'DIV') {
            instructions.push(['DIV']);
        } else if (instruction === 'DUP') {
            instructions.push(['DUP']);
        } else if (instruction === 'SWAP') {
            instructions.push(['SWAP']);
        } else if (instruction === 'PRINT') {
            instructions.push(['PRINT']);
        } else if (instruction === 'LABEL') {
            const labelName = parts[1];
            labels[labelName] = i + 1;
        } else if (instruction === 'JMP') {
            const labelName = parts[1];
            instructions.push(['JMP', labelName]);
        } else if (instruction === 'JZ') {
            const labelName = parts[1];
            instructions.push(['JZ', labelName]);
        } else if (instruction === 'JNZ') {
            const labelName = parts[1];
            instructions.push(['JNZ', labelName]);
        } else {
            throw new Error(`Unknown instruction '${instruction}' at line ${i + 1}`);
        }
    }
    
    // Execute instructions
    let pc = 0; // program counter
    let currentLineNum = 1;
    
    while (pc < instructions.length && stepCount < 1000) {
        stepCount++;
        
        const instruction = instructions[pc];
        currentLineNum = lineNumbers[pc];
        
        if (instruction[0] === 'PUSH') {
            stack.push(instruction[1]);
        } else if (instruction[0] === 'POP') {
            if (stack.length === 0) {
                throw new Error(`Stack underflow at line ${currentLineNum}`);
            }
            stack.pop();
        } else if (instruction[0] === 'ADD') {
            if (stack.length < 2) {
                throw new Error(`Stack underflow at line ${currentLineNum}`);
            }
            const b = stack.pop();
            const a = stack.pop();
            stack.push(a + b);
        } else if (instruction[0] === 'SUB') {
            if (stack.length < 2) {
                throw new Error(`Stack underflow at line ${currentLineNum}`);
            }
            const b = stack.pop();
            const a = stack.pop();
            stack.push(a - b);
        } else if (instruction[0] === 'MUL') {
            if (stack.length < 2) {
                throw new Error(`Stack underflow at line ${currentLineNum}`);
            }
            const b = stack.pop();
            const a = stack.pop();
            stack.push(a * b);
        } else if (instruction[0] === 'DIV') {
            if (stack.length < 2) {
                throw new Error(`Stack underflow at line ${currentLineNum}`);
            }
            const b = stack.pop();
            const a = stack.pop();
            if (b === 0) {
                throw new Error(`Division by zero at line ${currentLineNum}`);
            }
            stack.push(Math.trunc(a / b));
        } else if (instruction[0] === 'DUP') {
            if (stack.length === 0) {
                throw new Error(`Stack underflow at line ${currentLineNum}`);
            }
            stack.push(stack[stack.length - 1]);
        } else if (instruction[0] === 'SWAP') {
            if (stack.length < 2) {
                throw new Error(`Stack underflow at line ${currentLineNum}`);
            }
            const a = stack.pop();
            const b = stack.pop();
            stack.push(a);
            stack.push(b);
        } else if (instruction[0] === 'PRINT') {
            if (stack.length === 0) {
                throw new Error(`Stack underflow at line ${currentLineNum}`);
            }
            output.push(stack[stack.length - 1].toString());
        } else if (instruction[0] === 'JMP') {
            const labelName = instruction[1];
            pc = labels[labelName] - 1;
            continue;
        } else if (instruction[0] === 'JZ') {
            if (stack.length === 0) {
                throw new Error(`Stack underflow at line ${currentLineNum}`);
            }
            const value = stack.pop();
            if (value === 0) {
                pc = labels[instruction[1]] - 1;
                continue;
            }
        } else if (instruction[0] === 'JNZ') {
            if (stack.length === 0) {
                throw new Error(`Stack underflow at line ${currentLineNum}`);
            }
            const value = stack.pop();
            if (value !== 0) {
                pc = labels[instruction[1]] - 1;
                continue;
            }
        }
        
        pc++;
    }
    
    return { output: output };
}