def run(program: str) -> list[str]:
    data = {}
    # stack of dictionaries representing changes at each transaction level
    stack = []
    output = []

    lines = [line.strip() for line in program.split('\n') if line.strip()]

    for line in lines:
        parts = line.split()
        if not parts:
            continue
        
        cmd = parts[0]
        args = parts[1:]

        if cmd == "SET":
            if len(args) >= 2:
                key, value = args[0], args[1]
                if not stack:
                    data[key] = value
                else:
                    stack[-1][key] = value
        
        elif cmd == "GET":
            if len(args) >= 1:
                key = args[0]
                found_val = None
                # Search from the innermost transaction outwards to global data
                for tx in reversed(stack):
                    if key in tx:
                        found_val = tx[key]
                        break
                if found_val is None:
                    if key in data:
                        found_val = data[key]
                
                if found_val == "__DELETED__":
                    output.append("NULL")
                elif found_val is None:
                    output.append("NULL")
                else:
                    output.append(str(found_val))
        
        elif cmd == "DELETE":
            if len(args) >= 1:
                key = args[0]
                # Check if key exists in any transaction or global data
                exists = False
                for tx in stack:
                    if key in tx:
                        exists = True
                        break
                if not exists and key in data:
                    exists = True
                
                if exists:
                    if not stack:
                        data[key] = "__DELETED__"
                    else:
                        stack[-1][key] = "__DELETED__"
        
        elif cmd == "BEGIN":
            stack.append({})
        
        elif cmd == "COMMIT":
            if not stack:
                output.append("NO TRANSACTION")
            else:
                top = stack.pop()
                if not stack:
                    # Merge into global data
                    for k, v in top.items():
                        data[k] = v
                else:
                    # Merge into parent transaction
                    for k, v in top.items():
                        stack[-1][k] = v
        
        elif cmd == "ROLLBACK":
            if not stack:
                output.append("NO TRANSACTION")
            else:
                stack.pop()

    return output
