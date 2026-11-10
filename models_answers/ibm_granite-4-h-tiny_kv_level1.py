class InMemoryKVStore:
    def __init__(self):
        self.data = {}
        self.transactions = []

    def set(self, key, value):
        self.data[key] = value

    def get(self, key):
        return self.data.get(key, "NULL")

    def delete(self, key):
        if key in self.data:
            del self.data[key]

    def begin_transaction(self):
        self.transactions.append({})

    def commit(self):
        if not self.transactions:
            return "NO TRANSACTION"
        transaction = self.transactions.pop()
        parent = self.transactions[-1] if self.transactions else None
        for k, v in transaction.items():
            parent[k] = v

    def rollback(self):
        if not self.transactions:
            return "NO TRANSACTION"
        self.transactions.pop()

def run(program: str) -> list[str]:
    store = InMemoryKVStore()
    output = []
    lines = (line.strip() for line in program.splitlines() if line.strip())
    for line in lines:
        parts = line.split()
        cmd = parts[0]
        if cmd == "SET":
            key, value = parts[1], " ".join(parts[2:])
            store.set(key, value)
        elif cmd == "GET":
            key = parts[1]
            output.append(store.get(key))
        elif cmd == "DELETE":
            key = parts[1]
            store.delete(key)
        elif cmd == "BEGIN":
            store.begin_transaction()
        elif cmd == "COMMIT":
            output.append(store.commit())
        elif cmd == "ROLLBACK":
            output.append(store.rollback())
    return output
