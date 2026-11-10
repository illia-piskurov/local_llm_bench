def run(program: str) -> list[str]:
    import sys

    base_store = {}
    tx_stack = []  # stack of dicts for open transactions, innermost at the end
    watch_keys = set()  # keys that have been requested with WATCH command (not yet emitted)
    output = []

    lines = program.strip().splitlines()
    # We'll process each non-empty line.
    for raw in lines:
        if not raw.strip():
            continue
        parts = raw.split()
        cmd = parts[0].upper()

        if cmd == "SET":
            # SET <key> <value>
            if len(parts) != 3:
                # Invalid? Assume format correct; ignore extra?
                pass
            key, value_str = parts[1], parts[2]
            try:
                value = str(value_str)
            except ValueError:
                # If non-string numeric, keep as is but we'll handle later.
                value = value_str

            if tx_stack:
                inner_dict = tx_stack[-1]
                if key in inner_dict:
                    old_val = inner_dict[key]
                else:
                    old_val = None  # treat missing as NULL
                new_val = value
                if old_val is not None and str(old_val) == value:
                    # no change, nothing to do
                    pass
                else:
                    # perform update in the innermost transaction dict
                    inner_dict[key] = new_val
                    # If key is watched, emit notification immediately
                    if key in watch_keys:
                        # need old effective value: before update? The "old" we already have.
                        output.append(f"WATCH {key} {old_val if old_val is not None else 'NULL'} -> {new_val}")
            else:
                # global store
                old_val = base_store.get(key)
                new_val = value
                if (old_val is not None and str(old_val) == value) or (old_val is None and key not in base_store):
                    # Actually we need to decide: If key absent, it's change.
                    pass
                # For simplicity, always update global store unless same value? But spec about no notification for SET assigning same value. We'll check equality with old_val if exists.
                if old_val is None and new_val == base_store.get(key):  # weird case: not exist but assign same? ignore?
                    pass
                else:
                    # Update base_store
                    base_store[key] = new_val
                    if key in watch_keys:
                        output.append(f"WATCH {key} {old_val if old_val is not None else 'NULL'} -> {new_val}")
            # If key existed and value same, do nothing? We already handled.

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
                # Return value as string? They probably expect original representation. We'll just output str(val).
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
            # push a new empty dict onto stack
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
                    # only one transaction existed; commit to global store
                    for k, v in inner_dict.items():
                        base_store[k] = v
                # no output

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
            # WATCH <key>
            if len(parts) != 2:
                pass
            key = parts[1]
            if key not in watch_keys:
                watch_keys.add(key)

        else:
            # Unknown command, ignore
            pass

    return output
