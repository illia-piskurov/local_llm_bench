import sys

class InMemoryKeyValueStore:
    def __init__(self):
        self.global_store = {}
        self.transactions = []

    def run(self, program: str) -> list[str]:
        output = []
        commands = [cmd.strip() for cmd in program.split('\n') if cmd.strip()]
        self.transactions = []  # Reset transactions stack

        for cmd in commands:
            parts = cmd.split()
            if not parts:
                continue
            op, *args = parts

            if op == 'BEGIN':
                self.transactions.append({})
            elif op == 'COMMIT':
                if not self.transactions or len(self.transactions) < 2:
                    output.append("NO TRANSACTION")
                else:
                    parent_transaction = self.transactions[-2]
                    transaction = self.transactions.pop()
                    for key, value in transaction.items():
                        parent_transaction[key] = value
            elif op == 'ROLLBACK':
                if not self.transactions:
                    output.append("NO TRANSACTION")
                else:
                    self.transactions.pop()
            elif op == 'SET' and len(args) >= 2:
                key, value = args[0], args[1]
                current_transaction = self.transactions[-1] if self.transactions else self.global_store
                current_transaction[key] = value
            elif op == 'GET':
                if not self.transactions:
                    val = self.global_store.get(args[0], "NULL")
                else:
                    val = self.transactions[-1].get(args[0], "NULL")
                output.append(val)
            elif op == 'DELETE' and len(args) >= 1:
                key = args[0]
                if not self.transactions:
                    del self.global_store[key]
                else:
                    current_transaction = self.transactions[-1]
                    if key in current_transaction:
                        del current_transaction[key]

        return output

def main():
    store = InMemoryKeyValueStore()
    program = '\n'.join(sys.stdin.readlines())
    results = store.run(program)
    for res in results:
        print(res)

if __name__ == "__main__":
    main()
