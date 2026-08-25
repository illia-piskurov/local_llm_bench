class KeyValueStore:
    def __init__(self):
        self.store = {}
        self.transactions = []

    def set(self, key, value):
        if not self.transactions or not self.transactions[-1]:
            self.store[key] = value

    def get(self, key):
        return self.store.get(key, "NULL")

    def delete(self, key):
        if key in self.store:
            del self.store[key]

    def begin(self):
        self.transactions.append([])

    def commit(self):
        if not self.transactions or not self.transactions[-1]:
            print("NO TRANSACTION")
        else:
            changes = self.transactions.pop()
            for change in changes:
                if change[0] == "SET":
                    self.set(*change)
                elif change[0] == "DELETE":
                    self.delete(change[1])

    def rollback(self):
        if not self.transactions or not self.transactions[-1]:
            print("NO TRANSACTION")
        else:
            self.transactions.pop()

def run(program: str) -> list[str]:
    lines = program.strip().split('\n')
    store = KeyValueStore()
    output = []

    for line in lines:
        if line.startswith('SET'):
            _, key, value = line.split()
            store.set(key, value)
        elif line.startswith('GET'):
            key = line.split()[1]
            output.append(store.get(key))
        elif line.startswith('DELETE'):
            key = line.split()[1]
            store.delete(key)
        elif line.startswith('BEGIN'):
            store.begin()
        elif line.startswith('COMMIT'):
            store.commit()
        elif line.startswith('ROLLBACK'):
            store.rollback()

    return output
