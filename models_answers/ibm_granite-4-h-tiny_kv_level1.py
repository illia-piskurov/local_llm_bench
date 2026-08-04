class InMemoryKVStore:
    def __init__(self):
        self.store = {}
        self.transactions = []

    def run(self, program: str) -> list[str]:
        output = []
        for line in program.splitlines():
            if not line.strip():
                continue

            parts = line.split()
            command = parts[0]

            try:
                if command == "SET":
                    key, value = parts[1], parts[2]
                    self.store[key] = value
                elif command == "GET":
                    key = parts[1]
                    output.append(self.store.get(key, "NULL"))
                elif command == "DELETE":
                    key = parts[1]
                    if key in self.store:
                        del self.store[key]
                elif command == "BEGIN":
                    self.transactions.append(dict(self.store))
                elif command == "COMMIT":
                    if not self.transactions:
                        output.append("NO TRANSACTION")
                    else:
                        self.store.update(self.transactions.pop())
                elif command == "ROLLBACK":
                    if not self.transactions:
                        output.append("NO TRANSACTION")
                    else:
                        for key, value in self.transactions[-1].items():
                            self.store[key] = value
                        self.transactions.pop()
                else:
                    raise ValueError(f"Unknown command: {command}")
            except IndexError:
                pass

        return output


def run(program: str) -> list[str]:
    store = InMemoryKVStore()
    return store.run(program)
