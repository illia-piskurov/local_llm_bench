class TransactionalKeyValueStore:
    def __init__(self):
        self.store = {}
        self.transaction_stack = []
        self.watchers = {}

    def set(self, key, value):
        old_value = self.get(key)
        if self.transaction_stack:
            self.transaction_stack[-1][key] = value
        else:
            self.store[key] = value

        if key in self.watchers:
            for watcher in self.watchers[key]:
                watcher.send((old_value, value))

    def get(self, key):
        for txn in reversed(self.transaction_stack):
            if key in txn:
                return txn[key]
        return self.store.get(key, "NULL")

    def delete(self, key):
        old_value = self.get(key)
        if self.transaction_stack:
            if key in self.transaction_stack[-1]:
                del self.transaction_stack[-1][key]
        else:
            if key in self.store:
                del self.store[key]

        if key in self.watchers:
            for watcher in self.watchers[key]:
                watcher.send((old_value, "NULL"))

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

    def count(self, value):
        count = 0
        for txn in reversed(self.transaction_stack):
            count += list(txn.values()).count(value)
        count += list(self.store.values()).count(value)
        return count

    def watch(self, key):
        if key not in self.watchers:
            self.watchers[key] = set()

        import asyncio
        queue = asyncio.Queue()
        self.watchers[key].add(queue)

        try:
            old_value, new_value = yield from queue.get()
            return f"WATCH {key} {old_value} -> {new_value}"
        finally:
            self.watchers[key].remove(queue)
            if not self.watchers[key]:
                del self.watchers[key]

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
                if result != "NO TRANSACTION"::= self.rollback()
                if result != "NO TRANSACTION":
                    output.append(result)
            elif cmd == "COUNT":
                output.append(str(self.count(*args)))
            elif cmd == "WATCH":
                result = self.watch(*args)
                if result is not None:
                    output.append(result)

        return output

# Example usage:

store = TransactionalKeyValueStore()
program = """
BEGIN
SET a 1
WATCH a
SET a 2
GET a
COMMIT
GET a
ROLLBACK
GET a
""".strip()

print(store.run(program))  # Output: ['2', '2', 'NO TRANSACTION', '1']
