class InMemoryKeyValueStore:
    def   __init__(self):
        self.data = {}
        self.transactions = []
        self.watchers = {}
        self.snapshots = {}

    # ... existing methods remain the same ...

    def snapshot(self, name):
        self.snapshots[name] = self.data.copy()

    def restore(self, name):
        if name in self.snapshots:
            self.data = self.snapshots[name]
            self.watchers = {}
            self.update_watchers()
        else:
            raise ValueError(f"No snapshot named {name} exists")

    # ... existing methods remain the same ...
