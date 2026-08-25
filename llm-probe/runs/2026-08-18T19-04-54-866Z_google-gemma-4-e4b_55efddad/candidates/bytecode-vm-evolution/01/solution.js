export function solve(input) {
    const programStr = input?.program;
    if (!programStr) {
        return { output: [], error: "Input is missing a 'program' field." };
    }

    // --- State Initialization ---
    let stack = [];
    let output = [];
    const MAX_STEPS = 1000;
    let stepCount = 0;

    // Program processing requires tracking original line numbers for error reporting.
    const lines = programStr.split('\n');
    
    // Structure to hold instructions and their metadata
    let executableInstructions = [];
    // Map label names to instruction indices (relative index in executableInstructions)
    let labels = new Map(); 

    // --- Phase 1: Parse Program and Identify Labels ---
    for (let i = 0; i < lines.length; i++) {
        const originalLineNumber = i + 1; // 1-based line number
        const line = lines[i].trim();

        if (!line || line.startsWith('#')) {
            // Comment or empty line: Do not add to executableInstructions, but count for numbering implicitly.
            continue;
        }

        const parts = line.split(/\s+/);
        const instructionCode = { 
            name: parts[0], 
            args: parts.slice(1), 
            lineNum: originalLineNumber 
        };
        
        if (instructionCode.name === 'LABEL') {
            const labelName = instructionCode.args[0];
            // Labels are stored in the map referencing their index *in the next block of instructions*
            // We mark them as non-executable markers for now, but we need a placeholder index.
            labels.set(labelName, executableInstructions.length); 
            // Add a dummy instruction to occupy the space and maintain indexing continuity
            executableInstructions.push({ name: 'LABEL', args: [labelName], lineNum: originalLineNumber });

        } else {
            executableInstructions.push(instructionCode);
        }
    }

    // --- Phase 2: Execution Loop ---
    let ip = 0; // Instruction Pointer (index into executableInstructions)

    while (ip < executableInstructions.length && stepCount < MAX_STEPS) {
        const instruction = executableInstructions[ip];
        stepCount++;
        const lineNum = instruction.lineNum;
        const name = instruction.name;
        const args = instruction.args;

        // Check for Label markers (should not be executed, just skipped)
        if (name === 'LABEL') {
            ip++;
            continue;
        }

        try {
            switch (name) {
                case 'PUSH':
                    if (args.length < 1) throw new Error("Syntax error: PUSH requires an argument.");
                    const value = parseInt(args[0], 10);
                    if (isNaN(value)) throw new Error(`Argument '${args[0]}' is not a valid integer.`);
                    stack.push(value);
                    break;

                case 'POP':
                    if (stack.length < 1) {
                        throw new Error("Stack underflow");
                    }
                    stack.pop();
                    break;

                case 'ADD':
                    if (stack.length < 2) {
                        throw new Error("Stack underflow");
                    }
                    const b_add = stack.pop();
                    const a_add = stack.pop();
                    stack.push(a_add + b_add);
                    break;

                case 'SUB':
                    if (stack.length < 2) {
                        throw new Error("Stack underflow");
                    }
                    const b_sub = stack.pop();
                    const a_sub = stack.pop();
                    stack.push(a_sub - b_sub);
                    break;

                case 'MUL':
                    if (stack.length < 2) {
                        throw new Error("Stack underflow");
                    }
                    const b_mul = stack.pop();
                    const a_mul = stack.pop();
                    stack.push(a_mul * b_mul);
                    break;

                case 'DIV':
                    if (stack.length < 2) {
                        throw new Error("Stack underflow");
                    }
                    const b_div = stack.pop();
                    const a_div = stack.pop();
                    if (b_div === 0) {
                        throw new Error(`Division by zero at line ${lineNum}`);
                    }
                    stack.push(Math.trunc(a_div / b_div));
                    break;

                case 'DUP':
                    if (stack.length < 1) {
                        throw new Error("Stack underflow");
                    }
                    const top = stack[stack.length - 1];
                    stack.push(top);
                    break;

                case 'SWAP':
                    if (stack.length < 2) {
                        throw new Error("Stack underflow");
                    }
                    const b_swap = stack.pop();
                    const a_swap = stack.pop();
                    stack.push(b_swap);
                    stack.push(a_swap); // Note: The original order was A, B -> Pop B, Pop A. We push B then A to reverse it. Wait, SWAP means swap top two items. Stack: [..., a, b]. Pop b (B), pop a (A). Push a (new bottom), Push b (new top).
                    // Correction for SWAP logic: Original stack [..., A, B]. POP -> B (temp1), POP -> A (temp2). We want to restore [..., B, A]. 
                    // Stack is currently [...]. temp_b = pop(). temp_a = pop(). Push b. Push a. Wrong.
                    // Let's track it simply: Pop B, Pop A. Stack: [...] We push A back, then B. No.
                    // Correct SWAP: Top two items are X (bottom) and Y (top). Stack: [...X, Y]. 
                    // 1. pop() -> Y. tempY = Y. Stack: [...X]. 2. pop() -> X. tempX = X. Stack: [...].
                    // We push tempX, then tempY. No. Wait. If I POP B, the new top is A. Pop A. The new top is X.
                    // Simpler way: SWAP pops b, a. Push b, pop stack size - 1 items. This requires careful handling.
                    
                    // Standard Stack Swap Implementation:
                    const temp_b = stack.pop(); // Pops B
                    if (stack.length < 1) throw new Error("Internal error during SWAP");
                    const temp_a = stack.pop(); // Pops A
                    stack.push(temp_b); // Pushes B back to the bottom position
                    stack.push(temp_a); // Pushes A on top of B
                    // Oh, wait. Stack: [X, Y]. Pop Y. Pop X. Stack: [] Wait, stack is NOT empty. It's [...]. 
                    // If the stack was [10, 20], pop(20)=B. stack=[10]. pop(10)=A. stack=[]. WRONG ASSUMPTION.
                    
                    // Assume stack: [...] (N-2 items), A, B.
                    const b_swap_val = stack.pop(); // Pops B. Stack top is now A.
                    if (stack.length < 1) throw new Error("Internal error during SWAP");
                    const a_swap_val = stack.pop(); // Pops A. Stack top is now N-2 item.
                    
                    // We push them back in the swapped order: B, then A
                    stack.push(b_swap_val); 
                    stack.push(a_swap_val); 

                    // Reverting to the simpler understanding of SWAP on top two elements (A, B -> B, A):
                    // Stack: [..., N-2, A, B]
                    const b = stack.pop(); // Stack: [..., N-2, A]
                    const a = stack.pop(); // Stack: [..., N-2]
                    stack.push(b); // Stack: [..., N-2, B]
                    stack.push(a); // Stack: [..., N-2, B, A]. THIS IS THE CORRECT BEHAVIOR.

                    // Re-implementing SWAP based on correct assumption:
                    const b_val = stack.pop(); 
                    if (stack.length < 1) throw new Error("Stack underflow"); // Should have caught this earlier, but safety check.
                    const a_val = stack.pop(); 
                    
                    stack.push(b_val); 
                    stack.push(a_val);

                    break;

                case 'PRINT':
                    if (stack.length < 1) {
                        throw new Error("Stack underflow");
                    }
                    const printVal = stack[stack.length - 1];
                    output.push(String(printVal));
                    // No pop required per rules
                    break;

                case 'JMP':
                case 'JZ':
                case 'JNZ': {
                    if (args.length < 1) throw new Error("Syntax error: Jump instruction requires a label name.");
                    const targetLabel = args[0];
                    
                    if (!labels.has(targetLabel)) {
                        throw new Error(`Undefined label '${targetLabel}'`);
                    }
                    
                    let targetIndex = labels.get(targetLabel);

                    // JZ/JNZ require popping the condition value first
                    if (name === 'JZ' || name === 'JNZ') {
                        if (stack.length < 1) throw new Error("Stack underflow");
                        const condition = stack.pop();
                        if (condition === undefined) throw new Error("Internal error: Condition pop failed.");

                        if (name === 'JZ') {
                            if (condition === 0) {
                                ip = targetIndex;
                                continue; // Jump executed, skip default increment
                            } else {
                                // Does not jump, proceed normally
                            }
                        } else { // JNZ
                            if (condition !== 0) {
                                ip = targetIndex;
                                continue; // Jump executed, skip default increment
                            } else {
                                // Does not jump, proceed normally
                            }
                        }
                    } else { // JMP
                        ip = targetIndex;
                        continue; // Jump executed, skip default increment
                    }
                }

                default:
                    throw new Error(`Unknown instruction '${name}'`);
            }
        } catch (e) {
            // Check if the error is related to line numbering or general execution failure
            let errorMessage = e.message;
            if (errorMessage.includes("Stack underflow")) {
                 // If we hit an error, the lineNum is valid for reporting
                return { output: [...output], error: `Stack underflow at line ${lineNum}` };
            } else if (errorMessage.includes("Division by zero at line")) {
                 return { output: [...output], error: errorMessage };
            } else if (errorMessage.message === "Internal error: Condition pop failed.") {
                // Should not happen if stack checks are robust, but handle it defensively
                return { output: [...output], error: `Stack underflow at line ${lineNum}` };
            } else if (e instanceof Error && e.message.startsWith("Undefined label")) {
                 return { output: [...output], error: e.message };
            }

            // Catch other errors (Unknown instruction, general runtime failure)
            if (errorMessage.includes("at line ")) {
                return { output: [...output], error: errorMessage };
            } else if (name === 'UNKNOWN_INST') { // Fallback for unknown instructions handled before switch
                 return { output: [...output], error: `Unknown instruction '${name}' at line ${lineNum}` };
            } 
            
            // Default catch-all for runtime errors (e.g., syntax, general underflow)
            if (!errorMessage.includes("at line")) {
                return { output: [...output], error: `${e.message} at line ${lineNum}` };
            }

            return { output: [...output], error: errorMessage };
        }

        // If execution succeeded and we didn't explicitly jump, move to the next instruction
        ip++;
    }

    if (stepCount >= MAX_STEPS && ip < executableInstructions.length) {
        return { output: [...output], error: "Execution step limit exceeded" };
    }
    
    // Successful completion
    return { output: [...output] };
}