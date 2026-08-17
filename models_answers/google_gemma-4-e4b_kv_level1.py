import copy
from typing import List, Dict, Any

class TransactionalKVStore:
    """
    In-memory key-value store supporting nested transactions.
    The state is managed using a stack of deep copies to ensure isolation.
    """
    def __init__(self):
        # The global persistent storage (the base level)
        self._store: Dict[str, Any] = {}
        # Stack of transaction scopes. Each element is a full copy of the state 
        # at the moment BEGIN was called.
        self._transaction_stack: List[Dict[str, Any]] = []

    def _get_current_view(self) -> Dict[str, Any]:
        """Returns the dictionary representing the current active view."""
        if self._transaction_stack:
            return self._transaction_stack[-1]
        return self._store

    def set(self, key: str, value: Any):
        """Sets a key-value pair in the current active scope."""
        current_view = self._get_current_view()
        # Note: Since we are modifying the dictionary reference at the top of the stack 
        # or the global store, changes are immediately visible.
        current_view[key] = value

    def get(self, key: str) -> Any:
        """Gets the value associated with a key in the current active scope."""
        current_view = self._get_current_view()
        return current_view.get(key, None)

    def delete(self, key: str):
        """Deletes a key from the current active scope."""
        current_view = self._get_current_view()
        if key in current_view:
            del current_view[key]

    def begin(self):
        """Starts a new transaction scope by creating a deep copy of the current state."""
        # We must capture the entire current view to ensure isolation.
        new_scope = copy.deepcopy(self._get_current_view())
        self._transaction_stack.append(new_scope)

    def commit(self) -> str:
        """Commits the innermost transaction, merging changes into the parent scope."""
        if not self._transaction_stack:
            return "NO TRANSACTION"

        # 1. Get the committed changes (the top scope)
        committed_scope = self._transaction_stack.pop()
        
        # 2. Determine the target scope for merging
        if not self._transaction_stack:
            # If this was the outermost transaction, merge into the global store
            target_store = self._store
        else:
            # Otherwise, merge into the parent transaction's view
            target_store = self._get_current_view()

        # 3. Merge changes from committed_scope to target_store
        for key, value in committed_scope.items():
            if key == "__DELETED__": # Sentinel for deleted keys
                if key in target_store:
                    del target_store[key]
            else:
                target_store[key] = value

        return "" # Successful commit does not produce output per requirements

    def rollback(self) -> str:
        """Rolls back the innermost transaction by discarding its changes."""
        if not self._transaction_stack:
            return "NO TRANSACTION"
        
        # Simply discard the top scope, effectively rolling back all changes made within it.
        self._transaction_stack.pop()
        return "" # Successful rollback does not produce output per requirements

    def run(self, program: str) -> List[str]:
        """
        Processes a sequence of commands and returns a list of output strings 
        for GET results or NO TRANSACTION messages.
        """
        lines = [line.strip() for line in program.split('\n') if line.strip()]
        output: List[str] = []

        for line in lines:
            parts = line.split()
            if not parts:
                continue

            command = parts[0].upper()

            try:
                if command == "SET":
                    if len(parts) < 3: continue
                    key, value_str = parts[1], parts[2]
                    # Attempt to convert simple types (like numbers) if possible, otherwise treat as string.
                    try:
                        value = int(value_str)
                    except ValueError:
                        try:
                            value = float(value_str)
                        except ValueError:
                            value = value_str
                    self.set(key, value)

                elif command == "GET":
                    if len(parts) < 2: continue
                    key = parts[1]
                    result = self.get(key)
                    output.append(str(result) if result is not None else "NULL")

                elif command == "DELETE":
                    if len(parts) < 2: continue
                    key = parts[1]
                    self.delete(key)

                elif command == "BEGIN":
                    self.begin()

                elif command == "COMMIT":
                    result = self.commit()
                    if result:
                        output.append(result)

                elif command == "ROLLBACK":
                    result = self.rollback()
                    if result:
                        output.append(result)

            except Exception as e:
                # In a real system, we would handle specific errors. 
                # Here, we just skip or log unexpected failures.
                pass
        
        return output


def run_kv_store() -> TransactionalKVStore:
    """Returns an instance of the KV store."""
    return TransactionalKVStore()

if __name__ == '__main__':
    # Example Usage (for testing purposes, not part of the required output)
    store = run_kv_store()
    program = """
SET user_id 100
SET name Alice
GET name
BEGIN
SET email alice@example.com
GET email
COMMIT
GET email
BEGIN
DELETE name
SET age 30
GET name
ROLLBACK
GET name
"""
    results = store.run(program)
    print("--- Test Results ---")
    for r in results:
        print(r)
