def run(program: str) -> list[str]:
    class KVStore:
        def __init__(self):
            self.main_store = {}
            self.transaction_stack = []
            self.watched_keys = set()
            self.DELETED = object()
            self.snapshots = {}

        def get(self, key):
            for layer in reversed(self.transaction_stack):
                if key in layer:
                    val = layer[key]
                    return str(val) if val is not self.DELETED else "NULL"
            
            if key in self.main_store:
                val = self.main_store[key]
                return str(val) if val is not self.DELETED else "NULL"
            return "NULL"

        def set(self, key, value):
            if self.transaction_stack:
                self.transaction_stack[-1][key] = value
            else:
                self.main_store[key] = value

        def delete(self, key):
            if self.transaction_stack:
                self.transaction_stack[-1][key] = self.DELETED
            else:
                self.main_store[key] = self.DELETED

        def begin(self):
            self.transaction_stack.append({})

        def commit(self):
            if not self.transaction_stack:
                return "NO TRANSACTION"
            
            changes = self.transaction_stack.pop()
            
            if self.transaction_stack:
                self.transaction_stack[-1].update(changes)
            else:
                for k, v in changes.items():
                    if v is self.DELETED:
                        self.main_store.pop(k, None)
                    else:
                        self.main_store[k] = v
            return None

        def rollback(self):
            if not self.transaction_stack:
                return "NO TRANSACTION"
            self.transaction_stack.pop()
            return None

        def count(self, value):
            all_keys = set(self.main_store.keys())
            for layer in self.transaction_stack:
                all_keys.update(layer.keys())
            
            count = 0
            for k in all_keys:
                if self.get(k) == value:
                    count += 1
            return str(count)

        def watch(self, key):
            self.watched_keys.add(key)

        def snapshot(self, name):
            self.snapshots[name] = {
                'main_store': self.main_store.copy(),
                'transaction_stack': [layer.copy() for layer in self.transaction_stack],
                'watched_keys': self.watched_keys.copy()
            }

        def restore(self, name):
            if name in self.snapshots:
                state = self.snapshots[name]
                self.main_store = state['main_store'].copy()
                self.transaction_stack = [layer.copy() for layer in state['transaction_stack']]
                self.watched_keys = state['watched_keys'].copy()

    store = KVStore()
    results = []
    
    for line in program.splitlines():
        line = line.strip()
        if not line:
            continue
        
        parts = line.split()
        if not parts:
            continue
        command = parts[0]
        
        if command == "SET":
            if len(parts) >= 3:
                key = parts[1]
                value = " ".join(parts[2:])
                old_val = store.get(key)
                store.set(key, value)
                new_val = store.get(key)
                if key in store.watched_keys and old_val != new_val:
                    results.append(f"WATCH {key} {old_val} -> {new_val}")
        elif command == "GET":
            if len(parts) >= 2:
                results.append(store.get(parts[1]))
        elif command == "DELETE":
            if len(parts) >= 2:
                key = parts[1]
                old_val = store.get(key)
                store.delete(key)
                new_val = store.get(key)
                if key in store.watched_keys and old_val != new_val:
                    results.append(f"WATCH {key} {old_val} -> {new_val}")
        elif command == "BEGIN":
            store.begin()
        elif command == "COMMIT":
            res = store.commit()
            if res:
                results.append(res)
        elif command == "ROLLBACK":
            res = store.rollback()
            if res:
                results.append(res)
        elif command == "COUNT":
            if len(parts) >= 2:
                results.append(store.count(parts[1]))
        elif command == "WATCH":
            if len(parts) >= 2:
                store.watch(parts[1])
        elif command == "SNAPSHOT":
            if len(parts) >= 2:
                store.snapshot(parts[1])
        elif command == "RESTORE":
            if len(parts) >= 2:
                store.restore(parts[1])
                
    return results
