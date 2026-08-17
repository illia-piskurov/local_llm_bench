def run(program: str) -> list[str]:
    store = {}
    stack = []                     # each element is a dict {key: (new_val, old_val)}
    output = []

    for line in program.splitlines():
        if not line.strip():
            continue
        parts = line.split()
        cmd = parts[0]

        if cmd == "SET":
            key, value = parts[1], parts[2]
            old = store.get(key)
            store[key] = value
            tx = stack[-1] if stack else None
            if tx:
                tx[key] = (value, old)

        elif cmd == "GET":
            val = store.get(parts[1])
            output.append(val if val is not None else "NULL")

        elif cmd == "DELETE":
            key = parts[1]
            if key in store:
                old = store[key]
                del store[key]
                tx = stack[-1] if stack else None
                if tx:
                    tx[key] = (None, old)

        elif cmd == "BEGIN":
            stack.append({})

        elif cmd == "COMMIT":
            if not stack:
                output.append("NO TRANSACTION")
            else:
                tx = stack.pop()
                parent = stack[-1] if stack else None
                for k, (new_val, old_val) in tx.items():
                    if parent is not None:
                        parent[k] = (new_val, old_val)

        elif cmd == "ROLLBACK":
            if not stack:
                output.append("NO TRANSACTION")
            else:
                tx = stack.pop()
                for k, (new_val, old_val) in tx.items():
                    if new_val is not None:
                        store[k] = old_val
                    else:
                        del store[k]
                # clear dict (not strictly needed)

    return output
