import sys

class InMemoryKeyValueStore:
    def __init__(self):
        self.global_store = {}
        self.transactions = []

    def _push_transaction(self):
        self.transactions.append({})

    def _pop_transaction(self):
        if not self.transactions:
            return None
        return self.transactions.pop()

    def run(self, program: str) -> list[str]:
        output = []
        commands = [cmd.strip() for cmd in program.split('\n') if cmd.strip()]
        current_transactions = []

        # Parse and execute commands
        for cmd in commands:
            parts = cmd.split()
            if not parts:
                continue

            if parts[0] == 'BEGIN':
                self._push_transaction()
                current_transactions.append(self.transactions[-1])

            elif parts[0] == 'COMMIT':
                if len(current_transactions) < 2 or not self.transactions[-1]:
                    output.append("NO TRANSACTION")
                else:
                    parent = current_transactions.pop()
                    changes = self._pop_transaction()
                    for key, value in changes.items():
                        if key in parent:
                            parent[key] = value
                        else:
                            parent[key] = value

            elif parts[0] == 'ROLLBACK':
                if not self.transactions[-1]:
                    output.append("NO TRANSACTION")
                else:
                    self._pop_transaction()

            elif parts[0] == 'SET' and len(parts) >= 3:
                key, value = parts[1], parts[2]
                current_store = self.transactions[-1] if self.transactions else self.global_store
                current_store[key] = value

            elif parts[0] == 'GET':
                key = parts[1]
                # Check all transactions from innermost to outermost
                for store in reversed(self.transactions):
                    if key in store:
                        output.append(store[key])
                        break
                else:
                    if key in self.global_store:
                        output.append(self.global_store[key])
                    else:
                        output.append("NULL")

            elif parts[0] == 'DELETE' and len(parts) >= 2:
                key = parts[1]
                current_store = self.transactions[-1] if self.transactions else self.global_store
                if key in current_store:
                    del current_store[key]

        return output

def main():
    store = InMemoryKeyValueStore()
    program = sys.stdin.read().strip()
    results = store.run(program)
    for res in results:
        print(res)

if __name__ == "__main__":
    main()
