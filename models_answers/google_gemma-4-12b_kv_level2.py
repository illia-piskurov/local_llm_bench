def run(program: str) -> list[str]:
    # Internal state of the key-value store
    data = {}
    # Stack to handle nested transaction levels
    stack = []
    # Sentinel object to represent a deleted key within a transaction scope
    _DELETED = object()
    # Set of keys that have been explicitly set or deleted (to be used by COUNT)
    known_keys = set()
    # Set of keys being watched for changes
    watched_keys = set()
    results = []

    def get_current_val(key):
        """Helper to determine the current visible value of a key."""
        for i in range(len(stack) - 1, -1, -1):
            if key in stack[i]:
                val = stack[i][key]
                return "NULL" if val is _DELETED else str(val)
        if key in data:
            return str(data[key])
        return "NULL"

    for line in program.splitlines():
        line = line.strip()
        if not line:
            continue
        
        parts = line.split()
        if not parts:
            continue
        
        cmd = parts[0]
        
        if cmd == "SET":
            # SET <key> <value>
            key, val = parts[1], parts[2]
            known_keys.add(key)
            old_val = get_current_val(key)
            
            if stack:
                stack[-1][key] = val
            else:
                data[key] = val
            
            new_val = get_current_val(key)
            # If the value changed and it's being watched, notify.
            if old_val != new_val and key in watched_keys:
                results.append(f"WATCH {key} {old_val} -> {new_val}")
        
        elif cmd == "GET":
            # GET <key>
            key = parts[1]
            results.append(get_current_val(key))
            
        elif cmd == "DELETE":
            # DELETE <key>
            key = parts[1]
            known_keys.add(key)
            old_val = get_current_val(key)
            
            if stack:
                stack[-1][key] = _DELETED
            else:
                if key in data:
                    del data[key]
            
            new_val = get_current_val(key)
            # If the value changed and it's being watched, notify.
            if old_val != new_val and key in watched_keys:
                results.append(f"WATCH {key} {old_val} -> {new_val}")
        
        elif cmd == "BEGIN":
            # BEGIN - start a new transaction level.
            stack.append({})
            
        elif cmd == "COMMIT":
            # COMMIT - merge the current transaction into the parent scope.
            if not stack:
                results.append("NO TRANSACTION")
            else:
                top = stack.pop()
                if stack:
                    for k, v in top.items():
                        stack[-1][k] = v
                else:
                    for k, v in top.items():
                        if v is _DELETED:
                            if k in data:
                                del data[k]
                        else:
                            data[k] = v
            
        elif cmd == "ROLLBACK":
            # ROLLBACK - discard the current transaction's changes.
            if not stack:
                results.append("NO TRANSACTION")
            else:
                stack.pop()

        elif cmd == "COUNT":
            # COUNT <value> - count keys whose current value equals <value>.
            target_val = parts[1]
            count = 0
            for k in known_keys:
                if get_current_val(k) == target_val:
                    count += 1
            results.append(str(count))

        elif cmd == "WATCH":
            # WATCH <key> - add key to the watch list.
            watched_keys.add(parts[1])
            
    return results
