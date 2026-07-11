def run(program: str) -> list[str]:
    # Internal state of the key-value store
    data = {}
    # Stack to handle nested transaction levels
    stack = []
    # Sentinel object to represent a deleted key within a transaction scope
    _DELETED = object()
    results = []

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
            # If a transaction is active, update the top-most level's view.
            # Otherwise, update the global store.
            key, val = parts[1], parts[2]
            if stack:
                stack[-1][key] = val
            else:
                data[key] = val
        
        elif cmd == "GET":
            # GET <key>
            # Search from the top of the transaction stack down to the global store.
            key = parts[1]
            res = "NULL"
            for i in range(len(stack) - 1, -1, -1):
                if key in stack[i]:
                    val = stack[i][key]
                    # If value is the sentinel, it means it was deleted in this scope.
                    res = "NULL" if val is _DELETED else val
                    break
            else:
                # Not found in any transaction level; check global store.
                if key in data:
                    res = data[key]
                else:
                    res = "NULL"
            results.append(str(res))
            
        elif cmd == "DELETE":
            # DELETE <key>
            # If a transaction is active, mark the key as deleted in that scope.
            # Otherwise, remove it from the global store.
            key = parts[1]
            if stack:
                stack[-1][key] = _DELETED
            else:
                if key in data:
                    del data[key]
                    
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
                    # Merge changes into the next level down in the stack.
                    for k, v in top.items():
                        stack[-1][k] = v
                else:
                    # Merge changes directly into the global store.
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
                
    return results
