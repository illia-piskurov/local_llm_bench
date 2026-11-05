class InMemoryKeyValueStore:
    def  __init__(self):
        self.data = {}
        self.transactions = []
        self.watchers = {}

    # ... existing methods remain the same ...

    def count(self, value):
        count = sum(1 for key, value_ in self.data.items() if value_ == value)
        return str(count)

    def watch(self, key):
        if key in self.data:
            old_value = self.data.get(key, None)
            self.data[key] = None
            self.watchers[key] = (self.data[key], old_value)
            return "OK"
        else:
            return "NULL"

    def update_watchers(self):
        for key, (new_value, old_value) in self.watchers.items():
            if new_value != old_value:
                print(f"WATCH {key} {old_value} -> {new_value}")

    def run(self, program):
        output = super().run(program)
        self.update_watchers()
        return output
