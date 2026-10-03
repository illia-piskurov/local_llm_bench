class InMemoryKVStore:
    def __init__(self):
        self.store = {}
        self.transactions = []
        self.watchers = {}

    def execute(self, line):
        parts = line.split()
        cmd = parts[0]
        if cmd == "SET":
            key, value = parts[1], parts[2]
            old_value = self.store.get(key)
            self.store[key] = value
            if key in self.watchers:
                for watcher_key, watcher_value in self.watchers[key]:
                    if watcher_key not in self.transactions[-1]:
                        print(f"WATCH {key} {watcher_value} -> {value}")
        elif cmd == "GET":
            key = parts[1]
            return [self.store.get(key, "NULL")]
        elif cmd == "DELETE":
            key = parts[1]
            if key in self.store:
                old_value = self.store[key]
                del self.store[key]
                if key in self.watchers:
                    for watcher_key, watcher_value in self.watchers[key]:
                        if watcher_key not in self.transactions[-1]:
                            print(f"WATCH {key} {watcher_value} -> NULL")
        elif cmd == "BEGIN":
            self.transactions.append({})
        elif cmd == "COMMIT":
            if not self.transactions:
                return ["NO TRANSACTION"]
            txn = self.transactions.pop()
            if self.transactions:
                parent_txn = self.transactions[-1]
                parent_txn.update(txn)
            else:
                self.store.update(txn)
        elif cmd == "ROLLBACK":
            if not self.transactions:
                return ["NO TRANSACTION"]
            self.transactions.pop()
        elif cmd == "COUNT":
            value = parts[1]
            count = sum(1 for v in self.store.values() + [v for txn in self.transactions for v in txn.values()] if v == value)
            return [str(count)]
        elif cmd == "WATCH":
            key = parts[1]
            old_value = self.store.get(key, "NULL")
            if key not in self.watchers:
                self.watchers[key] = []
            self.watchers[key].append((key, old_value))

    def run(self, program):
        output = []
        for line in program.strip().splitlines():
            if not line:
                continue
            result = self.execute(line)
            if isinstance(result, list):
                output.extend(result)
        return output

def run(program: str) -> list[str]:
    kv_store = InMemoryKVStore()
    return kv_store.run(program)
