class KVStore:
    def __init__(self):
        self.storage = {}
        self.tx_stack = []  # list of change dicts, innermost last

    def set(self, key, value):
        if self.tx_stack:
            self.tx_stack[-1][key] = value
        else:
            self.storage[key] = value

    def get(self, key):
        for tx in reversed(self.tx_stack):
            if key in tx:
                return tx[key]
        return self.storage.get(key, "NULL")

    def delete(self, key):
        if key in self.storage:
            del self.storage[key]

    def begin(self):
        self.tx_stack.append({})

    def commit(self):
        if not self.tx_stack:
            return "NO TRANSACTION"
        tx = self.tx_stack.pop()
        if self.tx_stack:
            self.tx_stack[-1].update(tx)
        else:
            self.storage.update(tx)
        return ""

    def rollback(self):
        if not self.tx_stack:
            return "NO TRANSACTION"
        self.tx_stack.pop()
        return ""


def run(program: str) -> list[str]:
    store = KVStore()
    outputs = []
    for line in program.splitlines():
        if not line.strip():
            continue
        parts = line.split()
        cmd = parts[0]
        if cmd == "SET":
            store.set(parts[1], parts[2])
        elif cmd == "GET":
            outputs.append(store.get(parts[1]))
        elif cmd == "DELETE":
            store.delete(parts[1])
        elif cmd == "BEGIN":
            store.begin()
        elif cmd == "COMMIT":
            outputs.append(store.commit())
        elif cmd == "ROLLBACK":
            outputs.append(store.rollback())
    return outputs
