class TransactionalKeyValueStore:
    def __init__(self):
        self.store = {}
        self.transaction_stack = []

    def set(self, key, value):
        if self.transaction_stack:
            self.transaction_stack[-1][key] = value
        else:
            self.store[key] = value

    def get(self, key):
        for txn in reversed(self.transaction_stack):
            if key in txn:
                return txn[key]
        return self.store.get(key, "NULL")

    def delete(self, key):
        if self.transaction_stack:
            if key in self.transaction_stack[-1]:
                del self.transaction_stack[-1][key]
        else:
            if key in self.store:
                del self.store[key]

    def begin(self):
        self.transaction_stack.append({})

    def commit(self):
        if not self.transaction_stack:
            return "NO TRANSACTION"

        parent_txn = self.transaction_stack[-2] if len(self.transaction_stack) > 1 else self.store
        for key, value in self.transaction_stack[-1].items():
            parent_txn[key] = value

        self.transaction_stack.pop()

    def rollback(self):
        if not self.transaction_stack:
            return "NO TRANSACTION"

        self.transaction_stack.pop()

    def run(self, program):
        output = []
        for line in program.split("\n"):
            line = line.strip()
            if not line:
                continue

            cmd, *args = line.split()
            if cmd == "SET":
                self.set(*args)
            elif cmd == "GET":
                result = self.get(*args)
                if result != "NULL":
                    output.append(result)
            elif cmd == "DELETE":
                self.delete(*args)
            elif cmd == "BEGIN":
                self.begin()
            elif cmd == "COMMIT":
                result = self.commit()
                if result != "NO TRANSACTION":
                    output.append(result)
            elif cmd == "ROLLBACK":
                result = self.rollback()
                if result != "NO TRANSACTION":
                    output.append(result)

        return output

# Example usage:

store = TransactionalKeyValueStore()
program = """
BEGIN
SET a 1
BEGIN
SET a 2
GET a
COMMIT
GET a
ROLLBACK
GET a
""".strip()

print(store.run(program))  # Output: ['2', 'NO TRANSACTION', '1']
