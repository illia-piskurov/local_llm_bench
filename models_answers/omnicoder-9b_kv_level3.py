def run(program):
    store = {}  # Main key-value store
    watch_keys = {}  # Track watched keys and their current values
    transaction_stack = []  # Each element is a dict of {key: (old_value, new_value)}
    snapshots = {}  # Store named snapshots
    
    output = []
    
    def handle_watch_notifications(key, old_val, new_val):
        if old_val != new_val:
            old_str = str(old_val) if old_val is not None else "NULL"
            new_str = str(new_val) if new_val is not None else "NULL"
            output.append(f"WATCH {key} {old_str} -> {new_str}")
    
    for line in program.split('\n'):
        parts = line.strip().split()
        if not parts:
            continue
        
        cmd = parts[0]
        
        if cmd == 'SET':
            key, value = parts[1], parts[2]
            
            # Handle watch notifications before setting
            old_val = store.get(key)
            handle_watch_notifications(key, old_val, value)
            
            # Track change in current transaction
            if transaction_stack:
                transaction_stack[-1][key] = (old_val, value)
            
            store[key] = value
            
        elif cmd == 'GET':
            key = parts[1]
            val = store.get(key)
            output.append(str(val))
            
        elif cmd == 'DELETE':
            key = parts[1]
            if key in store:
                old_val = store.pop(key)
                
                # Handle watch notifications before deleting
                handle_watch_notifications(key, old_val, None)
            
        elif cmd == 'SNAPSHOT':
            name = parts[1]
            # Save complete state including store, transaction_stack, watch_keys
            snapshots[name] = {
                'store': dict(store),  # Copy the store
                'transaction_stack': [dict(t) for t in transaction_stack],  # Deep copy each element
                'watch_keys': dict(watch_keys)  # Copy watch keys
            }
            
        elif cmd == 'RESTORE':
            name = parts[1]
            if name in snapshots:
                saved_state = snapshots[name]
                store.clear()
                store.update(saved_state['store'])
                
                transaction_stack.clear()
                for t in saved_state['transaction_stack']:
                    transaction_stack.append(t)
                    
                watch_keys.clear()
                watch_keys.update(saved_state['watch_keys'])
            else:
                # Unknown snapshot - treat as error or ignore
                pass
                
        elif cmd == 'WATCH':
            key = parts[1]
            current_val = store.get(key)
            if key not in watch_keys:
                watch_keys[key] = (current_val, None)  # Store current value and old value for notification
            
    return output
