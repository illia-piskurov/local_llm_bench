def run(program: str) -> list[str]:
    lines = program.strip().split('\n')
    stack = [{}]
    output = []

    for line in lines:
        if not line.strip():
            continue

        parts = line.split()
        cmd = parts[0]

        if cmd == 'SET':
            key, value = parts[1], parts[2]
            stack[-1][key] = value
        elif cmd == 'GET':
            key = parts[1]
            for i in range(len(stack) - 1, -1, -1):
                if key in stack[i]:
                    output.append(stack[i][key])
                    break
            else:
                output.append('NULL')
        elif cmd == 'DELETE':
            key = parts[1]
            for i in range(len(stack) - 1, -1, -1):
                if key in stack[i]:
                    del stack[i][key]
                    break
        elif cmd == 'BEGIN':
            stack.append({})
        elif cmd == 'COMMIT':
            if len(stack) > 1:
                top = stack.pop()
                for k, v in top.items():
                    stack[-1][k] = v
            else:
                output.append('NO TRANSACTION')
        elif cmd == 'ROLLBACK':
            if len(stack) > 1:
                stack.pop()
            else:
                output.append('NO TRANSACTION')

    return output
