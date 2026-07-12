class Store:
    def __init__(self):
        # The global store holds the base values of the keys.
        self.global_store = {}
        # A stack where each element is a dictionary representing 
        # changes made in that specific transaction level.
        self.transaction_stack = []
        # Internal marker to distinguish between a value and a deletion.
        self._TOMBSTONE = object()
        # Set of keys currently being watched for changes.
        self.watched_keys = set()
        # Set of all unique keys ever mentioned in SET, DELETE, or WATCH commands.
        self.all_known_keys = set()

    def get(self, key: str) -> str:
        # Search from the innermost transaction outwards to the global store.
        for i in range(len(self.transaction_stack) - 1, -1, -1):
            if key in self.transaction_stack[i]:
                val = self.transaction_stack[i][key]
                # If it's a tombstone or not found, return "NULL".
                return val if val is not self._TOMBSTONE else "NULL"
        
        if key in self.global_store:
            val = self.global_store[key]
            return val if val is not self._TOMBSTONE else "NULL"
        return "NULL"

    def set(self, key: str, value: str) -> list[str]:
        self.all_known_keys.add(key)
        old_val = self.get(key)
        if not self.transaction_stack:
            self.global_store[key] = value
        else:
            self.transaction_stack[-1][key] = value
        new_val = self.get(key)
        
        # If the key is watched and its visible value changed, return a notification.
        if key in self.watched_keys and old_val != new_val:
            return [f"WATCH {key} {old_val} -> {new_val}"]
        return []

    def delete(self, key: str) -> list[str]:
        self.all_known_keys.add(key)
        old_val = self.get(key)
        if not self.transaction_stack:
            if key in self.global_store:
                self.global_store[key] = self._TOMBSTONE
        else:
            self.transaction_stack[-1][key] = self._TOMBSTONE
        new_val = self.get(key)

        # If the key is watched and its visible value changed, return a notification.
        if key in self.watched_keys and old_val != new_val:
            return [f"WATCH {key} {old_val} -> {new_val}"]
        return []

    def watch(self, key: str):
        self.watched_keys.add(key)
        self.all_known_keys.add(key)

    def count(self, value: str) -> str:
        # Count how many known keys currently have the specified value.
        cnt = 0
        for k in self.all_known_keys:
            if self.get(k) == value:
                cnt += 1
        return str(cnt)

    def begin(self):
        self.transaction_stack.append({})

    def commit(self) -> str | None:
        if not self.transaction_stack:
            return "NO TRANSACTION"
        
        # Pop the current transaction and merge its changes into the level below.
        top = self.transaction_stack.pop()
        if not self.transaction_stack:
            # If it was the only transaction, merge directly into global store.
            for k, v in top.items():
                self.global_store[k] = v
        else:
            # Merge into the parent's transaction dictionary.
            target = self.transaction_stack[-1]
            for k, v in top.items():
                target[k] = v
        return None

    def rollback(self) -> str | None:
        if not self.transaction_stack:
            return "NO TRANSACTION"
        # Discard the current transaction's changes.
        self.transaction_stack.pop()
        return None

def run(program: str) -> list[str]:
    store = Store()
    results = []
    lines = program.splitlines()
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        parts = line.split()
        if not parts:
            continue
            
        cmd = parts[0].upper()
        if cmd == "SET":
            # Expects SET <key> <value>
            if len(parts) >= 3:
                res = store.set(parts[1], " ".join(parts[2:]))
                results.extend(res)
        elif cmd == "GET":
            # Expects GET <key>
            if len(parts) >= 2:
                results.append(store.get(parts[1]))
        elif cmd == "DELETE":
            # Expects DELETE <key>
            if len(parts) >= 2:
                res = store.delete(parts[1])
                results.extend(res)
        elif cmd == "BEGIN":
            store.begin()
        elif cmd == "COMMIT":
            res = store.commit()
            if res is not None:
                results.append(res)
        elif cmd == "ROLLBACK":
            res = store.rollback()
            if res is not None:
                results.append(res)
        elif cmd == "COUNT":
            # Expects COUNT <value>
            if len(parts) >= 2:
                results.append(store.count(parts[1]))
        elif cmd == "WATCH":
            # Expects WATCH <key>
            if len(parts) >= 2:
                store.watch(parts[1])
                
    return results
