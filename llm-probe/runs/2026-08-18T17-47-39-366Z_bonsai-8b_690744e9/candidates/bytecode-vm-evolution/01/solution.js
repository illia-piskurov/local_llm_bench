export function solve(input) {
  const program = input.program.trim().split('\n');
  const stack = [];
  const output = [];
  const error = null;
  let lineNum = 1;

  for (let i = 0; i < program.length; i++) {
    const line = program[i].trim();
    if (!line || line.startsWith('#')) {
      continue;
    }

    if (stack.length === 0) {
      error = "Stack underflow at line " + lineNum;
      break;
    }

    const parts = line.split(' ');
    const instruction = parts[0];

    switch (instruction) {
      case 'PUSH':
        if (parts.length < 2 || !/^\d+$/.test(parts[1])) {
          error = "Stack underflow at line " + lineNum;
          break;
        }
        stack.push(parseInt(parts[1]));
        lineNum++;
        continue;

      case 'POP':
        if (stack.length === 0) {
          error = "Stack underflow at line " + lineNum;
          break;
        }
        stack.pop();
        lineNum++;

      case 'ADD':
        if (stack.length < 2) {
          error = "Stack underflow at line " + lineNum;
          break;
        }
        const b = stack.pop();
        const a = stack.pop();
        stack.push(a + b);
        lineNum++;

      case 'SUB':
        if (stack.length < 2) {
          error = "Stack underflow at line " + lineNum;
          break;
        }
        const b = stack.pop();
        const a = stack.pop();
        stack.push(a - b);
        lineNum++;

      case 'MUL':
        if (stack.length < 2) {
          error = "Stack underflow at line " + lineNum;
          break;
        }
        const b = stack.pop();
        const a = stack.pop();
        stack.push(a * b);
        lineNum++;

      case 'DIV':
        if (stack.length < 2) {
          error = "Stack underflow at line " + lineNum;
          break;
        }
        const b = stack.pop();
        const a = stack.pop();
        if (b === 0) {
          error = `Division by zero at line ${lineNum}`;
          break;
        }
        stack.push(Math.trunc(a / b));
        lineNum++;

      case 'DUP':
        if (stack.length === 0) {
          error = "Stack underflow at line " + lineNum;
          break;
        }
        const val = stack.pop();
        stack.push(val);
        lineNum++;

      case 'SWAP':
        if (stack.length < 2) {
          error = "Stack underflow at line " + lineNum;
          break;
        }
        [stack.pop(), stack.pop()] = [stack.pop(), stack.pop()];
        lineNum++;

      case 'PRINT':
        if (stack.length === 0) {
          error = "Stack underflow at line " + lineNum;
          break;
        }
        output.push(stack[stack.length - 1].toString());
        lineNum++;

      case 'LABEL':
        if (parts.length < 2) {
          error = "Unknown instruction '" + parts[1] + "' at line " + lineNum;
          break;
        }
        const name = parts[1];
        // No-op during execution
        lineNum++;

      case 'JMP':
        if (parts.length < 2) {
          error = "Unknown instruction '" + parts[1] + "' at line " + lineNum;
          break;
        }
        const name = parts[1];
        // No-op during execution
        lineNum++;

      case 'JZ':
        if (parts.length < 2) {
          error = "Unknown instruction '" + parts[1] + "' at line " + lineNum;
          break;
        }
        const name = parts[1];
        if (stack.pop() === 0) {
          // Pop value and proceed to label
          stack.pop();
          lineNum++;
          continue;
        }
        // Continue execution
        lineNum++;

      case 'JNZ':
        if (parts.length < 2) {
          error = "Unknown instruction '" + parts[1] + "' at line " + lineNum;
          break;
        }
        const name = parts[1];
        if (stack.pop() !== 0) {
          // Continue execution
          lineNum++;
          continue;
        }
        // Pop value and proceed to label
        stack.pop();
        lineNum++;

      default:
        error = "Unknown instruction '" + instruction + "' at line " + lineNum;
        break;
    }

    if (error) {
      return { output, error };
    }

    if (i + 1 >= program.length || i + 1 > 1000) {
      return { output, error: "Execution step limit exceeded" };
    }
  }

  return { output };
}