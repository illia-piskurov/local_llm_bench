def run(program: str) -> list[str]:
    store = {}
    tx_stack = []
    output = []

    for line in program.splitlines():
        if not line.strip():
            continue
        parts = line.split()
        cmd = parts[0]

        if cmd == "SET":
            key, val = parts[1], parts[2]
            store[key] = val
            cur_tx = tx_stack[-1]  # type: dict
            cur_tx[key] = val

        elif cmd == "GET":
            output.append(str(store.get(key, 'NULL')))

        elif cmd == "DELETE":
            key = parts[1]
            if key in store:
                del store[key]
                cur_tx = tx_stack[-1]  # type: dict
                cur_tx.pop(key, None)

        elif cmd == "BEGIN":
            tx_stack.append({})

        elif cmd == "COMMIT":
            if not tx_stack:
                output.append("NO TRANSACTION")
            else:
                inner = tx_stack.pop()
                if tx_stack:  # merge into parent
                    for k, v in inner.items():
                        cur_tx = tx_stack[-1]
                        cur_tx[k] = v

        elif cmd == "ROLLBACK":
            if not tx_stack:
                output.append("NO TRANSACTION")
            else:
                inner = tx_stack.pop()
                for k, v in inner.items():
                    del store[k]
                    parent = tx_stack[-1]  # type: dict
                    parent.pop(k, None)

    return output
