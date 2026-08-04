class KeyValueStore:
    def __init__(self):
        self.data = {}
        self.transactions = []

    def _commit(self):
        if not self.transactions:
            print("NO TRANSACTION")
            return

        top_tx = self.transactions.pop()
        for key, value in top_tx.items():
            self.data[key] = value
        print("COMMIT")

    def _rollback(self):
        if not self.transactions:
            print("NO TRANSACTION")
            return

        self.transactions.pop()
        for key, value in list(self.data.items()):
            del self.data[key]
        print("ROLLBACK")

    def execute_command(self, command):
        parts = command.split()
        if not parts:
            return

        op = parts[0]

        if op == "SET":
            if len(parts) != 3:
                continue
            key, value = parts[1], parts[2]
            self.data[key] = value

        elif op == "GET":
            if len(parts) != 2:
                continue
            key = parts[1]
            print(self.data.get(key, "NULL"))

        elif op == "DELETE":
            if len(parts) != 2:
                continue
            key = parts[1]
            if key in self.data:
                del self.data[key]

        elif op == "BEGIN":
            self.transactions.append({})
            print("BEGIN")

        elif op == "COMMIT":
            self._commit()

        elif op == "ROLLBACK":
            self._rollback()


def run(program: str) -> list[str]:
    kv_store = KeyValueStore()
    output = []

    for line in program.splitlines():
        line = line.strip()
        if not line:
            continue

        kv_store.execute_command(line)
        if line.startswith(("GET", "COMMIT", "ROLLBACK")):
            output.append(line)

    return output
