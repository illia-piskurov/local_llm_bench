class KeyValueStore:
    def __init__(self):
        self.store = {}
        self.transactions = []
        self.watchers = {}

    def set(self, key, value):
        if not self.transactions or not self.transactions[-1]:
            self.store[key] = value
            for watcher_key, (old_value, _) in self.watchers.items():
                if watcher_key == key:
                    print(f"WATCH {watcher_key} {old_value} -> {value}")
        else:
            changes = self.transactions[-1]
            changes.append(("SET", key, value))
            for watcher_key, (_, old_value) in self.watchers.items():
                if watcher_key == key and self.store.get(watcher_key, "NULL") != old_value:
                    print(f"WATCH {watcher_key} {old_value} -> {self.store.get(watcher_key, 'NULL')}")

    def get(self, key):
        return self.store.get(key, "NULL")

    def delete(self, key):
        if key in self.store:
            value = self.store[key]
            del self.store[key]
            for watcher_key, (_, old_value) in self.watchers.items():
                if watcher_key == key and self.store.get(watcher_key, "NULL") != old_value:
                    print(f"WATCH {watcher_key} {old_value} -> {self.store.get(watcher_key, 'NULL')}")
        else:
            for watcher_key, (_, _) in self.watchers.items():
                if watcher_key == key:
                    print(f"WATCH {watcher_key} NULL -> NULL")

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

    def watch(self, key):
        if key in self.watchers:
            old_value = self.store.get(key, "NULL")
            self.watchers[key] = (old_value, None)
        else:
            self.watchers[key] = ("NULL", None)

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
        elif line.startswith('WATCH'):
            key = line.split()[1]
            store.watch(key)

    return output
