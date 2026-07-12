def run(program: str) -> list[str]:
    store = {}
    tx_stack = []
    watch_active = {}          # key -> value before next change
    output = []
    snapshots = {}             # name -> snapshot dict

    for line in program.splitlines():
        if not line.strip():
            continue
        parts = line.split()
        cmd = parts[0]

        if cmd == "SET":
            key, val = parts[1], parts[2]
            old_val = store.get(key, 'NULL')
            # WATCH notification
            if key in watch_active and old_val != val:
                output.append(f"WATCH {key} {old_val} -> {val}")
            store[key] = val
            cur_tx = tx_stack[-1]
            cur_tx[key] = val

        elif cmd == "GET":
            output.append(str(store.get(key, 'NULL')))

        elif cmd == "DELETE":
            key = parts[1]
            if key in store:
                old_val = store[key]
                del store[key]
                # WATCH notification
                if key in watch_active and old_val != 'NULL':
                    output.append(f"WATCH {key} {old_val} -> NULL")
        elif cmd == "BEGIN":
            tx_stack.append({})

        elif cmd == "COMMIT":
            if not tx_stack:
                output.append("NO TRANSACTION")
            else:
                inner = tx_stack.pop()
                if tx_stack:  # merge into parent
                    cur_tx = tx_stack[-1]
                    for k, v in inner.items():
                        cur_tx[k] = v

        elif cmd == "ROLLBACK":
            if not tx_stack:
                output.append("NO TRANSACTION")
            else:
                inner = tx_stack.pop()
                for k, v in inner.items():
                    del store[k]
                    parent = tx_stack[-1]
                    parent.pop(k, None)

        elif cmd == "COUNT":
            value = parts[1]
            cnt = sum(1 for k, v in store.items() if v == value)
            output.append(str(cnt))

        elif cmd == "WATCH":
            key = parts[1]
            watch_active[key] = store.get(key, 'NULL')

        elif cmd == "SNAPSHOT":
            name = parts[1]
            snapshots[name] = {
                "store": store.copy(),
                "tx_stack": [dict(t) for t in tx_stack],
                "watch_active": watch_active.copy()
            }

        elif cmd == "RESTORE":
            name = parts[1]
            if name not in snapshots:
                # No output per spec; just ignore or keep current state
                continue
            store = snapshots[name]["store"]
            tx_stack = [dict(t) for t in snapshots[name]["tx_stack"]]
            watch_active = snapshots[name]["watch_active"].copy()

    return output
