class InMemoryKeyValueStore:
    def __init__(self):
        self.store = {}
        self.trx = None
        self.trx_active = False
        self.watch_keys = set()

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
            self.store = self.trx.copy()
            self.trx_active = False
            if self.trx:
                return "NO TRANSACTION"
        return ""

    def rollback(self):
        if self.trx_active:
            self.trx_active = False
            return "NO TRANSACTION"

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
            elif cmd == "WATCH":
                key = parts[1]
                value = self.get(key)
                if value is not None:
                    print(f"WATCH {key} {value} -> {value}")
                    self.watch_keys.add(key)
            else:
                pass
        return lines
