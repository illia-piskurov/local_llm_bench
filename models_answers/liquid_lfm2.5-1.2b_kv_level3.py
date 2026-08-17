class InMemoryKeyValueStore:
    def __init__(self):
        self.store = {}
        self.trx = None
        self.trx_active = False
        self.watch_keys = set()
        self.snapshots = {}

    def set(self, key, value):
        if self.trx_active:
            self.store[key] = value
        else:
            self.store[key] = value
            if not self.trx:
                self.trx = {}
            self.trx_active = True
            if key in self.watch_keys:
                self.watch_keys.remove(key)
        if key in self.watch_keys:
            print(f"WATCH {key} {self.store.get(key, 'NULL')} -> {value}")

    def get(self, key):
        if self.trx_active:
            if key in self.store:
                return self.store[key]
            else:
                return "NULL"
        return self.store.get(key, "NULL")

    def delete(self, key):
        if self.trx_active:
            if key in self.store:
                del self.store[key]
                if not self.trx:
                    self.trx = {}
            else:
                self.trx_active = False
                if key in self.watch_keys:
                    self.watch_keys.remove(key)
        return "NULL" if key not in self.store else "NULL"

    def begin(self):
        if not self.trx_active:
            self.trx_active = True
            self.trx = {}

    def commit(self):
        if self.trx_active:
            snapshot = self.snapshots.get(self.trx)
            if snapshot is None:
                snapshot = {}
            snapshot.update(self.store)
            self.store = snapshot
            self.trx_active = False
            return "NO TRANSACTION"
        return ""

    def rollback(self):
        if self.trx_active:
            self.trx_active = False
            snapshot = self.snapshots.get(self.trx)
            if snapshot is not None:
                self.store = snapshot.copy()
                self.trx_active = True
            return "NO TRANSACTION"
        return ""

    def snapshot(self, snapshot):
        self.snapshots[self.trx] = snapshot
        self.watch_keys.update(snapshot.get('watched', set()))

    def restore(self, name):
        if name in self.snapshots:
            self.trx = self.snapshots[name]
            self.watch_keys.update(self.snapshots[name]['watched'])
            return "RESTORE COMPLETE"
        else:
            return "SNAPSHOT NOT FOUND"

    def run(self, program):
        lines = []
        for line in program.strip().split():
            parts = line.split()
            cmd = parts[0]
            if cmd == "SET":
                key = parts[1]
                value = ' '.join(parts[2:])
                self.set(key, value)
            elif cmd == "GET":
                res = self.get(key)
                lines.append(f"GET {key}: {res}")
            elif cmd == "DELETE":
                key = parts[1]
                self.delete(key)
            elif cmd == "BEGIN":
                self.begin()
            elif cmd == "COMMIT":
                result = self.commit()
                if result:
                    lines.append(result)
            elif cmd == "ROLLBACK":
                result = self.rollback()
                if result:
                    lines.append(result)
            elif cmd == "SNAPSHOT":
                name = parts[1]
                self.snapshot(name)
                continue
            elif cmd == "WATCH":
                key = parts[1]
                value = self.get(key)
                if value is not None:
                    print(f"WATCH {key} {value} -> {value}")
                    self.watch_keys.add(key)
            elif cmd == "RESTORE":
                name = parts[1]
                result = self.restore(name)
                lines.append(result)
            else:
                pass
        return lines
