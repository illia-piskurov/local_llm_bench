def run(program: str) -> list[str]:
    lines = program.split('\n')
    store = {}
    tx_stack = []
    output = []

    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        parts = line.split()
        cmd = parts[0]
        
        if cmd == 'SET':
            key = parts[1]
            value = parts[2]
            store[key] = value
            
        elif cmd == 'GET':
            key = parts[1]
            val = store.get(key, "NULL")
            output.append(val)
            
        elif cmd == 'DELETE':
            key = parts[1]
            if key in store:
                del store[key]
                
        elif cmd == 'BEGIN':
            tx_stack.append(dict(store))
            
        elif cmd == 'COMMIT':
            if not tx_stack:
                output.append("NO TRANSACTION")
            else:
                tx_stack.pop()
                
        elif cmd == 'ROLLBACK':
            if not tx_stack:
                output.append("NO TRANSACTION")
            else:
                snapshot = tx_stack.pop()
                # Restore keys from snapshot
                for k, v in snapshot.items():
                    store[k] = v
                # Remove keys not in snapshot
                for k in list(store.keys()):
                    if k not in snapshot:
                        del store[k]
                        
    return output
