class InMemoryKVStore:
    def __init__(self):
        self.data = {}
        self.transactions = []  # Stack of transactions (each is a dict of key-value pairs)
        self.watchers = {}  # key -> list of watcher callbacks (to be called on change)

    def run(self, program: str) -> list[str]:
        output = []
        lines = [line.strip() for line in program.split('\n') if line.strip()]
        
        for line in lines:
            if not line:
                continue
                
            parts = line.split(' ', 1)
            cmd = parts[0]
            
            if cmd == "SET":
                key, value = parts[1], parts[1].split(' ', 1)[1] if len(parts) > 1 else ""
                if len(parts) > 1:
                    value = parts[1]
                if self.transactions:
                    current_tx = self.transactions[-1]
                    current_tx[key] = value
                else:
                    self.data[key] = value
                # Check for watchers
                if key in self.watchers:
                    # Get current visible value (from current transaction or global data)
                    current_value = self._get_visible_value(key)
                    if current_value != value:
                        output.append(f"WATCH {key} {current_value} -> {value}")
                        
            elif cmd == "GET":
                key = parts[1] if len(parts) > 1 else ""
                if self.transactions:
                    current_tx = self.transactions[-1]
                    if key in current_tx:
                        output.append(str(current_tx[key]))
                    else:
                        output.append("NULL")
                else:
                    if key in self.data:
                        output.append(str(self.data[key]))
                    else:
                        output.append("NULL")
                        
            elif cmd == "DELETE":
                key = parts[1] if len(parts) > 1 else ""
                if self.transactions:
                    current_tx = self.transactions[-1]
                    if key in current_tx:
                        del current_tx[key]
                else:
                    if key in self.data:
                        del self.data[key]
                # Check for watchers
                if key in self.watchers:
                    current_value = self._get_visible_value(key)
                    # Since DELETE sets to NULL, we check if it was previously set
                    if current_value is not None:
                        output.append(f"WATCH {key} {current_value} -> NULL")
                        
            elif cmd == "BEGIN":
                self.transactions.append({})
                
            elif cmd == "COMMIT":
                if not self.transactions:
                    output.append("NO TRANSACTION")
                else:
                    current_tx = self.transactions.pop()
                    if self.transactions:
                        # Merge current transaction into the parent
                        for key, value in current_tx.items():
                            self.transactions[-1][key] = value
                    else:
                        # This is the top-level transaction, merge into global data
                        for key, value in current_tx.items():
                            self.data[key] = value
                            
            elif cmd == "ROLLBACK":
                if not self.transactions:
                    output.append("NO TRANSACTION")
                else:
                    self.transactions.pop()
                    
            elif cmd == "COUNT":
                value = parts[1] if len(parts) > 1 else ""
                if self.transactions:
                    current_tx = self.transactions[-1]
                    # Count keys in current transaction with value
                    count = 0
                    for key in current_tx:
                        if current_tx[key] == value:
                            count += 1
                    # Also count in global data
                    for key in self.data:
                        if self.data[key] == value:
                            count += 1
                    output.append(str(count))
                else:
                    count = 0
                    for key in self.data:
                        if self.data[key] == value:
                            count += 1
                    output.append(str(count))
                    
            elif cmd == "WATCH":
                key = parts[1] if len(parts) > 1 else ""
                if key:
                    if key not in self.watchers:
                        self.watchers[key] = []
                    # Watcher is now active — will trigger on changes
                    # We don't output here, just register
                    
        return output
    
    def _get_visible_value(self, key):
        # Check current transaction stack
        if self.transactions:
            current_tx = self.transactions[-1]
            if key in current_tx:
                return current_tx[key]
        return self.data.get(key, None)


def run(program: str) -> list[str]:
    store = InMemoryKVStore()
    return store.run(program)
