export function solve(input) {
  const program = input.program.split('\n');
  let stack = [];
  let output = [];
  let lineNum = 0;
  let steps = 0;

  for (const line of program) {
    lineNum++;
    if (!line.trim() || line.startsWith('#')) continue; // Ignore empty lines and comments

    const [inst, ...args] = line.split(' ');
    steps++;

    if (steps > 1000) throw new Error('Execution step limit exceeded');

    switch (inst) {
      case 'PUSH':
        stack.push(parseInt(args[0]));
        break;
      case 'POP':
        if (!stack.length) throw new Error(`Stack underflow at line ${lineNum}`);
        stack.pop();
        break;
      case 'ADD':
        if (stack.length < 2) throw new Error(`Stack underflow at line ${lineNum}`);
        const b = stack.pop();
        const a = stack.pop();
        stack.push(a + b);
        break;
      case 'SUB':
        if (stack.length < 2) throw new Error(`Stack underflow at line ${lineNum}`);
        const d = stack.pop();
        const c = stack.pop();
        stack.push(c - d);
        break;
      case 'MUL':
        if (stack.length < 2) throw new Error(`Stack underflow at line ${lineNum}`);
        const f = stack.pop();
        const e = stack.pop();
        stack.push(e * f);
        break;
      case 'DIV':
        if (stack.length < 2) throw new Error(`Stack underflow at line ${lineNum}`);
        const h = stack.pop();
        const g = stack.pop();
        if (!g) throw new Error(`Division by zero at line ${lineNum}`);
        stack.push(Math.trunc(g / h));
        break;
      case 'DUP':
        if (!stack.length) throw new Error(`Stack underflow at line ${lineNum}`);
        stack.push(stack[stack.length - 1]);
        break;
      case 'SWAP':
        if (stack.length < 2) throw new Error(`Stack underflow at line ${lineNum}`);
        [stack[stack.length - 2], stack[stack.length - 1]] = [stack[stack.length - 1], stack[stack.length - 2]];
        break;
      case 'PRINT':
        if (!stack.length) throw new Error(`Stack underflow at line ${lineNum}`);
        output.push(stack[stack.length - 1].toString());
        break;
      case 'LABEL':
        // No-op
        break;
      case 'JMP':
        const target = args[0];
        let labelFound = false;
        for (const l of program) {
          if (!l.trim() || l.startsWith('#')) continue; // Ignore empty lines and comments
          const [labelInst, name] = l.split(' ');
          if (name === target) {
            lineNum = program.indexOf(l);
            labelFound = true;
            break;
          }
        }
        if (!labelFound) throw new Error(`Label '${target}' not found at line ${lineNum}`);
        continue; // Jump to the labeled line
      case 'JZ':
        const jzValue = stack.pop();
        if (!stack.length) throw new Error(`Stack underflow at line ${lineNum}`);
        const jmpTarget = args[0];
        let jmpFound = false;
        for (const l of program) {
          if (!l.trim() || l.startsWith('#')) continue; // Ignore empty lines and comments
          const [labelInst, name] = l.split(' ');
          if (name === jmpTarget && jzValue === 0) {
            lineNum = program.indexOf(l);
            jmpFound = true;
            break;
          }
        }
        if (!jmpFound) throw new Error(`Label '${jmpTarget}' not found at line ${lineNum}`);
        continue; // Jump to the labeled line
      case 'JNZ':
        const jnzValue = stack.pop();
        if (!stack.length) throw new Error(`Stack underflow at line ${lineNum}`);
        const jmp2Target = args[0];
        let jmp2Found = false;
        for (const l of program) {
          if (!l.trim() || l.startsWith('#')) continue; // Ignore empty lines and comments
          const [labelInst, name] = l.split(' ');
          if (name === jmp2Target && jnzValue !== 0) {
            lineNum = program.indexOf(l);
            jmp2Found = true;
            break;
          }
        }
        if (!jmp2Found) throw new Error(`Label '${jmp2Target}' not found at line ${lineNum}`);
        continue; // Jump to the labeled line
      default:
        throw new Error(`Unknown instruction '${inst}' at line ${lineNum}`);
    }
  }

  return { output, error: undefined };
}