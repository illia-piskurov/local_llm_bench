class Transaction:
    def __init__(self, snapshot):
        self.snapshot = snapshot
        self.changes = {}

class KeyStore:
    def __init__(self):
        self.data = {}
        self.stack = []
        self.watched = set()

    def get(self, key):
        for tx in reversed(self.stack):
            if key in tx.changes:
                val = tx.changes[key]
                if val is None:
                    return "NULL"
                return val
            if key in tx.snapshot:
                return tx.snapshot[key]
        if key in self.data:
            return self.data[key]
        return "NULL"

    def set(self, key, value, output):
        if key in self.watched:
            old_val = self.get(key)
            if old_val != value:
                output.append(f"WATCH {key} {old_val} -> {value}")
        if not self.stack:
            self.data[key] = value
        else:
            self.stack[-1].changes[key] = value

    def delete(self, key, output):
        if key in self.watched:
            old_val = self.get(key)
            if old_val != "NULL":
                output.append(f"WATCH {key} {old_val} -> NULL")
        if not self.stack:
            if key in self.data:
                del self.data[key]
        else:
            self.stack[-1].changes[key] = None

    def count(self, value):
        count = 0
        for k in self.data:
            if self.get(k) == value:
                count += 1
        return count

    def watch(self, key):
        self.watched.add(key)

    def begin(self):
        self.stack.append(Transaction(self.data.copy()))

    def commit(self):
        if not self.stack:
            return "NO TRANSACTION"
        tx = self.stack.pop()
        if self.stack:
            parent = self.stack[-1].snapshot
            for k, v in tx.changes.items():
                if v is None:
                    parent.pop(k, None)
                else:
                    parent[k] = v
        else:
            for k, v in tx.changes.items():
                if v is None:
                    self.data.pop(k, None)
                else:
                    self.data[k] = v

    def rollback(self):
        if not self.stack:
            return "NO TRANSACTION"
        self.stack.pop()

def run(program: str) -> list[str]:
    store = KeyStore()
    output = []
    lines = program.strip().split('\n')
    for line in lines:
        if not line.strip():
            continue
        parts = line.split()
        cmd = parts[0]
        if cmd == "SET":
            store.set(parts[1], parts[2], output)
        elif cmd == "GET":
            output.append(store.get(parts[1]))
        elif cmd == "DELETE":
            store.delete(parts[1], output)
        elif cmd == "COUNT":
            output.append(str(store.count(parts[1])))
        elif cmd == "WATCH":
            store.watch(parts[1])
        elif cmd == "BEGIN":
            store.begin()
        elif cmd == "COMMIT":
            res = store.commit()
            if res:
                output.append(res)
        elif cmd == "ROLLBACK":
            res = store.rollback()
            if res:
                output.append(res)
    return output
