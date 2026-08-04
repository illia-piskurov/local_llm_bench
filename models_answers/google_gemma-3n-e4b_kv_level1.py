class InMemoryKVStore:
    def __init__(self):
        self.data = {}
        self.transactions = []  # List of transaction dictionaries

    def set(self, key, value):
        if self.transactions:
            raise ValueError("Transaction is active")
        self.data[key] = value

    def get(self, key):
        if self.transactions:
            return "NULL"  # Return NULL while transaction is active
        return self.data.get(key, "NULL")

    def delete(self, key):
        if self.transactions:
            raise ValueError("Transaction is active")
        if key in self.data:
            del self.data[key]

    def begin(self):
        self.transactions.append({"parent": None, "changes": {}})

    def commit(self):
        if not self.transactions:
            print("NO TRANSACTION")
            return

        transaction = self.transactions[-1]
        parent = transaction["parent"]
        changes = transaction["changes"]

        if parent is None:  # Root transaction
            for key, value in changes.items():
                self.data[key] = value
            self.transactions.pop()
        else:
            parent.setdefault("changes", {})
            for key, value in changes.items():
                parent["changes"][key] = value
            self.transactions.pop()

    def rollback(self):
        if not self.transactions:
            print("NO TRANSACTION")
            return

        transaction = self.transactions[-1]
        parent = transaction["parent"]
        changes = transaction["changes"]

        if parent is None:  # Root transaction
            pass  # No changes to revert for root transaction
        else:
            for key, value in changes.items():
                del self.data[key]
            self.transactions.pop()


    def run(self, program):
        output = []
        lines = program.splitlines()
        for line in lines:
            line = line.strip()
            if not line:
                continue

            parts = line.split()
            command = parts[0]

            if command == "SET":
                if len(parts) != 3:
                    output.append("")
                    continue
                key, value = parts[1], parts[2]
                self.set(key, value)
            elif command == "GET":
                if len(parts) != 2:
                    output.append("")
                    continue
                key = parts[1]
                output.append(self.get(key))
            elif command == "DELETE":
                if len(parts) != 2:
                    output.append("")
                    continue
                key = parts[1]
                self.delete(key)
            elif command == "BEGIN":
                self.begin()
            elif command == "COMMIT":
                self.commit()
            elif command == "ROLLBACK":
                self.rollback()

        return output


if __name__ == '__main__':
    store = InMemoryKVStore()
    program = """
    SET key1 value1
    GET key1
    BEGIN
    SET key2 value2
    GET key2
    SET key3 value3
    GET key3
    ROLLBACK
    GET key3
    COMMIT
    GET key3
    """

    output = store.run(program)
    for item in output:
        print(item)
