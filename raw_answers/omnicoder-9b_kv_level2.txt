```python
def run(program):
    store = {}  # Main key-value store
    output = []
    
    def handle_watch_notifications(key, old_val, new_val):
        if old_val != new_val:
            old_str = str(old_val) if old_val is not None else "NULL"
            new_str = str(new_val) if new_val is not None else "NULL"
            output.append(f"WATCH {key} {old_str} -> {new_str}")
    
    # Track watched keys and their current values
    watch_keys = {}  # key -> (current_value, old_value_for_notification)
    
    def set_value(key, value):
        old_val = store.get(key)
        
        # Handle watch notifications before setting
        if key in watch_keys:
            watch_old_val, _ = watch_keys[key]
            if watch_old_val != value:
                handle_watch_notifications(key, watch_old_val, value)
        
        store[key] = value
        
    def delete_value(key):
        old_val = store.get(key)
        
        # Handle watch notifications before deleting
        if key in watch_keys:
            watch_old_val, _ = watch_keys[key]
            if watch_old_val != None and watch_old_val != old_val:
                handle_watch_notifications(key, watch_old_val, None)
        
        store.pop(key, None)
    
    # Transaction stack - each element tracks changes made in that transaction
    transaction_stack = []  # Each element is a dict of {key: (old_value, new_value)}
    
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
