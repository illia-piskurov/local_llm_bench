class KeyValueStore:
    def __init__(self):
        self.data = {}
        self.transactions = []
        self.watchers = {}

    def _commit(self):
        if not self.transactions:
            print("NO TRANSACTION")
            return

        top_tx = self.transactions.pop()
        for key, value in top_tx.items():
            self. data[key] = value
        print("COMMIT")

    def _rollback(self):
        if not self.transactions:
            print("NO TRANSACTION")
            return

        self.transactions.pop()
        for key, value in self.transactions[-1].items():
            del self.data[key]

    def execute_command(self, command):
        parts = command.split()
        if not parts:
            return

        op = parts[0]
        if op == "SET":
            if len(parts) != 3:
                return
            key, value = parts[1], parts[2]
            self.data[key] = value
            if key in self.watchers:
                old_value = self.data.get(key, "NULL")
                print(f"WATCH {key} {old_value} -> {value}")
        elif op == "GET":
            if len(parts) != 2:
                return
            key = parts[1]
            print(self.data.get(key, "NULL"))
        elif op == "DELETE":
            if len(parts) != 2:
                return
            key = parts[1]
            if key in self.data:
                del self.data[key]
        elif op == "BEGIN":
            self.transactions.append({})
        elif op == "COMMIT":
            self._commit()
        elif op == "ROLLBACK":
            self._rollback()
        elif op == "COUNT":
            if len(parts) != 2:
                return
            value = parts[1]
            count = sum(1 for v in (self.data.get(k, "NULL") for k in self.data) if v == value)
            print(count)
        elif op == "WATCH":
            if len(parts) != 2:
                return
            key = parts[1]
            self.watchers[key] = True

def run(program: str) -> list[str]:
    store = KeyValueStore()
    output = []
    for line in program.splitlines():
        if not line.strip():
            continue
        store.execute_command(line)
        if 'COMMIT' in line or 'ROLLBACK' in line:
            output.append(line)
    return output
