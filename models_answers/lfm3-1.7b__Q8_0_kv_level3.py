def run(program: str) -> list[str]:
    import sys

    base_store = {}
    tx_stack = []  # stack of dicts for open transactions, innermost at the end
    watch_keys = set()  # keys that have been requested with WATCH command (not yet emitted)
    output = []
    snapshots = {}  # name -> { 'base_store': dict, 'tx_stack': list[dict], 'watch_keys': set }

    lines = program.strip().splitlines()
    for raw in lines:
        if not raw.strip():
            continue
        parts = raw.split()
        cmd = parts[0].upper()

        if cmd == "SET":
            # SET <key> <value>
            if len(parts) != 3:
                pass
            key, value_str = parts[1], parts[2]
            try:
                value = str(value_str)
            except ValueError:
                value = value_str

            if tx_stack:
                inner_dict = tx_stack[-1]
                if key in inner_dict:
                    old_val = inner_dict[key]
                else:
                    old_val = None
                new_val = value
                if old_val is not None and str(old_val) == value:
                    pass
                else:
                    inner_dict[key] = new_val
                    if key in watch_keys:
                        output.append(f"WATCH {key} {old_val if old_val is not None else 'NULL'} -> {new_val}")
            else:
                old_val = base_store.get(key)
                new_val = value
                if (old_val is not None and str(old_val) == value) or (old_val is None and key not in base_store):
                    pass
                elif not (old_val is None and new_val == base_store.get(key)):
                    # Update global store unless already same?
                    base_store[key] = new_val
                    if key in watch_keys:
                        output.append(f"WATCH {key} {old_val if old_val is not None else 'NULL'} -> {new_val}")
        elif cmd == "GET":
            key = parts[1]
            if tx_stack:
                inner_dict = tx_stack[-1]
                val = inner_dict.get(key)
            else:
                val = base_store.get(key)
            if val is None:
                output.append("NULL")
            else:
                output.append(str(val))
        elif cmd == "DELETE":
            key = parts[1]
            if tx_stack:
                inner_dict = tx_stack[-1]
                if key in inner_dict:
                    del inner_dict[key]
            else:
                if key in base_store:
                    del base_store[key]
        elif cmd == "BEGIN":
            tx_stack.append({})
        elif cmd == "COMMIT":
            if len(tx_stack) == 0:
                output.append("NO TRANSACTION")
            else:
                inner_dict = tx_stack.pop()
                if len(tx_stack) > 0:
                    parent = tx_stack[-1]
                    for k, v in inner_dict.items():
                        parent[k] = v
                else:
                    for k, v in inner_dict.items():
                        base_store[k] = v
        elif cmd == "ROLLBACK":
            if len(tx_stack) == 0:
                output.append("NO TRANSACTION")
            else:
                inner_dict = tx_stack.pop()
                if len(tx_stack) > 0:
                    parent = tx_stack[-1]
                    for k, v in inner_dict.items():
                        parent[k] = v
                else:
                    for k, v in inner_dict.items():
                        base_store[k] = v
        elif cmd == "WATCH":
            if len(parts) != 2:
                pass
            key = parts[1]
            if key not in watch_keys:
                watch_keys.add(key)
        elif cmd == "SNAPSHOT":
            if len(parts) != 2:
                pass
            snap_name = parts[1]
            # save current state: global base_store, tx_stack list (shallow copy), watch_keys
            snapshot_data = {
                'base_store': base_store.copy(),
                'tx_stack': tx_stack.copy(),
                'watch_keys': set(watch_keys)
            }
            snapshots[snap_name] = snapshot_data
        elif cmd == "RESTORE":
            if snap_name in snapshots:
                snap = snapshots[snap_name]
                base_store = snap['base_store']
                tx_stack = snap['tx_stack'].copy()
                watch_keys = snap['watch_keys']
            # else: unknown, do nothing (not tested)
        else:
            pass

    return output
