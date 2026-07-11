class InMemoryKV:
    def __init__(self):
        self.global_store = {}
        self.transactions = []  # stack of dicts for open transactions

    def _find_transaction(self, depth):
        """Return transaction dict at given depth or None."""
        if depth == 0:
            return self.transactions[-1] if self.transactions else None
        for i in range(len(self.transactions) - depth, -1, -1):
            if len(self.transactions[i]) > i:
                return self.transactions[i][depth]
        return None

    def set(self, key, value):
        # Apply to current transaction (create if needed)
        txn = self._find_transaction(len(self.transactions))
        if txn is None:
            txn = {}
            self.transactions.append(txn)
        txn[key] = value

    def get(self, key):
        # Search from innermost to global
        for txn in reversed(self.transactions):
            if key in txn:
                return txn[key]
        return "NULL"

    def delete(self, key):
        txn = self._find_transaction(len(self.transactions))
        if txn is not None and key in txn:
            del txn[key]

    def begin(self):
        # Start a new transaction (empty dict)
        self.transactions.append({})

    def commit(self):
        if not self.transactions:
            return "NO TRANSACTION"
        current = self.transactions.pop()
        if not self.transactions:
            # Merge into global
            for k, v in current.items():
                self.global_store[k] = v
        else:
            parent = self.transactions[-1]
            for k, v in current.items():
                parent[k] = v

    def rollback(self):
        if not self.transactions:
            return "NO TRANSACTION"
        txn = self.transactions.pop()
        # Discard changes
        return None


def run(program: str):
    kv = InMemoryKV()
    output = []
    lines = program.strip().split('\n')
    for line in lines:
        if not line.strip():
            continue
        parts = line.split()
        cmd = parts[0]
        if cmd == "SET":
            key, value = parts[1], parts[2]
            kv.set(key, value)
        elif cmd == "GET":
            key = parts[1]
            output.append(str(kv.get(key)))
        elif cmd == "DELETE":
            key = parts[1]
            kv.delete(key)
        elif cmd == "BEGIN":
            kv.begin()
        elif cmd == "COMMIT":
            res = kv.commit()
            if res is not None:
                output.append(res)
        elif cmd == "ROLLBACK":
            res = kv.rollback()
            if res is not None:
                output.append(res)
    return output
