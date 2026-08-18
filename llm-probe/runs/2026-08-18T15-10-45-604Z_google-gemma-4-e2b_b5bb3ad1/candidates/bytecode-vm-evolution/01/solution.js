export function solve(input) {
    const program = input.program;
    const lines = program.split('\n');

    let stack = [];
    let output = [];
    let pc = 0; // Program Counter (index into lines array)
    const MAX_STEPS = 1000;

    // Map to store label targets: { 'labelName': lineIndex }
    const labels = {};

    /** Helper function to report errors and stop execution */
    const handleError = (message, lineNum) => {
        return { output: output, error: `Error at line ${lineNum}: ${message}` };
    };

    // --- Phase 1: Pre-processing Labels ---
    // We don't strictly need to pre-process labels if we handle them during execution flow correctly,
    // but knowing the structure helps define the context for error reporting.

    /**
     * Main Execution Loop
     */
    while (pc < lines.length && stack.length > 0 && pc <= MAX_STEPS) {
        const line = lines[pc].trim();
        let parts = line.split(/\s+/).filter(p => p.length > 0);

        if (line === '') {
            // Ignore empty lines, but still count them for line numbering context if needed later.
            pc++;
            continue;
        }

        const currentLineNum = pc + 1; // 1-based indexing for error reporting

        try {
            const instruction = parts[0];

            switch (instruction) {
                case 'PUSH': {
                    const n = parseInt(parts[1], 10);
                    if (isNaN(n)) throw new Error("Invalid argument for PUSH");
                    stack.push(n);
                    break;
                }

                case 'POP': {
                    if (stack.length === 0) {
                        throw new Error("Stack underflow");
                    }
                    stack.pop();
                    break;
                }

                case 'ADD':
                case 'SUB':
                case 'MUL':
                case 'DIV': {
                    if (stack.length < 2) {
                        throw new Error("Stack underflow");
                    }
                    const b = stack.pop();
                    const a = stack.pop();

                    if (instruction === 'ADD') {
                        stack.push(a + b);
                    } else if (instruction === 'SUB') {
                        stack.push(a - b);
                    } else if (instruction === 'MUL') {
                        stack.push(a * b);
                    } else if (instruction === 'DIV') {
                        if (b === 0) {
                            throw new Error(`Division by zero at line ${currentLineNum}`);
                        }
                        // Math.trunc handles truncation towards zero as required
                        stack.push(Math.trunc(a / b));
                    }
                    break;
                }

                case 'DUP': {
                    if (stack.length === 0) {
                        throw new Error("Stack underflow");
                    }
                    const top = stack[stack.length - 1];
                    stack.push(top);
                    break;
                }

                case 'SWAP': {
                    if (stack.length < 2) {
                        throw new Error("Stack underflow");
                    }
                    // Pop b then a, push a then b
                    const a = stack.pop();
                    const b = stack.pop();
                    stack.push(b, a);
                    break;
                }

                case 'PRINT': {
                    if (stack.length === 0) {
                        throw new Error("Stack underflow");
                    }
                    // PRINT does not pop, it just prints the top element
                    output.push(String(stack[stack.length - 1]));
                    break;
                }

                case 'LABEL': {
                    const labelName = parts[1];
                    labels[labelName] = pc; // Store index of instruction following LABEL
                    // Label itself is a no-op execution step
                    break;
                }

                case 'JMP': {
                    const targetLabel = parts[1];
                    if (!(targetLabel in labels)) {
                        throw new Error(`Unknown label '${targetLabel}' at line ${currentLineNum}`);
                    }
                    pc = labels[targetLabel];
                    // pc will be incremented by the loop mechanism below, so we adjust it back if necessary
                    break;
                }

                case 'JZ': {
                    const targetLabel = parts[1];
                    if (!(targetLabel in labels)) {
                        throw new Error(`Unknown label '${targetLabel}' at line ${currentLineNum}`);
                    }
                    const value = stack.pop();
                    if (value === 0) {
                        pc = labels[targetLabel]; // Jump
                    }
                    // If condition is false, pc advances normally below
                    break;
                }

                case 'JNZ': {
                    const targetLabel = parts[1];
                    if (!(targetLabel in labels)) {
                        throw new Error(`Unknown label '${targetLabel}' at line ${currentLineNum}`);
                    }
                    const value = stack.pop();
                    if (value !== 0) {
                        pc = labels[targetLabel]; // Jump
                    }
                    // If condition is false, pc advances normally below
                    break;
                }

                default:
                    throw new Error(`Unknown instruction '${instruction}' at line ${currentLineNum}`);
            }

        } catch (e) {
            // Handle all runtime errors by stopping execution and formatting the output
            return handleError(e.message, currentLineNum);
        }

        pc++; // Advance PC if no jump occurred implicitly
    }


    if (pc >= MAX_STEPS && stack.length > 0) {
         return handleError("Execution step limit exceeded", lines[pc - 1] ? pc : "End of program");
    }

    return { output: output };
}