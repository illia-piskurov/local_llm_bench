class InMemoryKeyValueStore:
    def __init__(self):
        self.data = {}
        self.transactions = []

    def set(self, key, value):
        self.data[key] = value
        return "OK"

    def get(self, key):
        return self.data.get(key, "NULL")

    def delete(self, key):
        if key in self.data:
            del self.data[key]
        return "OK"

    def begin(self):
        self.transactions.append([])
        return "OK"

    def commit(self):
        if not self.transactions:
            return "NO TRANSACTION"
        changes = self.transactions[-1]
        self.transactions.pop()
        for command in changes:
            if command[0] == "SET":
                self.data[command[1]] = command[2]
            elif command[0] == "DELETE":
                if command[1] in self.data:
                    del self.data[command[1]]
        return "OK"

    def rollback(self):
        if not self.transactions:
            return "NO TRANSACTION"
        self.transactions.pop()
        return "OK"

    def run(self, program):
        commands = program.split("\n")
        output = []
        for command in commands:
            args = command.split()
            if args[0] == "SET":
                output.append(self.set(args[1], args[2]))
            elif args[0] == "GET":
                output.append(self.get(args[1]))
            elif args[0] == "DELETE":
                output.append(self.delete(args[1]))
            elif args[0] == "BEGIN":
                output.append(self.begin())
            elif args[0] == "COMMIT":
                output.append(self.commit())
            elif args[0] == "ROLLBACK":
                output.append(self.rollback())
        return output
