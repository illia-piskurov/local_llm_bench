import copy

class NestedKVStore:
    """
    Implements an in-memory key-value store supporting nested transactions.
    Uses a stack of snapshots to manage transaction states.
    """
    def __init__(self):
        # Global persistent storage (the state before any transaction)
        self.storage = {}
        # Stack holding copies of the KV store state at the start of each transaction level.
        # The top element is the current working state.
        self.transaction_stack = []

    def _get_current_state(self):
        """Returns a reference to the dictionary currently being modified."""
        if self.transaction_stack:
            return self.transaction_stack[-1]
        return self.storage

    def set_key(self, key: str, value: str) -> None:
        """Sets or updates a key-value pair in the current scope."""
        current_state = self._get_current_state()
        # Since we are modifying the state directly (which is either the global storage 
        # or the top element of the stack), this change is immediately visible.
        current_state[key] = value

    def get_key(self, key: str) -> str | None:
        """Retrieves the value associated with a key in the current scope."""
        current_state = self._get_current_state()
        return current_state.get(key)

    def delete_key(self, key: str) -> None:
        """Deletes a key from the current scope if it exists."""
        current_state = self._get_current_state()
        if key in current_state:
            del current_state[key]

    def begin(self) -> None:
        """Starts a new transaction level by saving a snapshot of the current state."""
        # Save a deep copy of the current effective state onto the stack.
        current_snapshot = self._get_current_state()
        new_state = copy.deepcopy(current_snapshot)
        self.transaction_stack.append(new_state)

    def commit(self) -> str:
        """Commits the innermost transaction, merging changes into the parent scope."""
        if not self.transaction_stack:
            return "NO TRANSACTION"

        # 1. Pop the inner state (the committed changes)
        inner_state = self.transaction_stack.pop()
        
        # 2. Determine the target for merging
        if not self.transaction_stack:
            # This was the outermost transaction, merge into global storage
            target_storage = self.storage
        else:
            # Merge into the parent's current working state (the new top of stack)
            target_storage = self.transaction_stack[-1]

        # 3. Perform the merge: inner changes overwrite outer changes
        for key, value in inner_state.items():
            target_storage[key] = value
        
        return "" # Successful commit produces no output

    def rollback(self) -> str:
        """Rolls back the innermost transaction by discarding the snapshot."""
        if not self.transaction_stack:
            return "NO TRANSACTION"
        
        # Simply discard the top state (the changes are lost when we pop it).
        self.transaction_stack.pop()
        return "" # Successful rollback produces no output

def run(program: str) -> list[str]:
    """
    Processes a program string containing commands and returns a list of outputs 
    for GET, COMMIT, and NO TRANSACTION cases.
    """
    store = NestedKVStore()
    output = []
    lines = [line.strip() for line in program.split('\n') if line.strip()]

    for line in lines:
        parts = line.split()
        if not parts:
            continue

        command = parts[0]

        try:
            if command == "SET":
                key, value = parts[1], parts[2]
                store.set_key(key, value)
            elif command == "GET":
                key = parts[1]
                result = store.get_key(key)
                output.append(str(result) if result is not None else "NULL")
            elif command == "DELETE":
                key = parts[1]
                store.delete_key(key)
            elif command == "BEGIN":
                store.begin()
            elif command == "COMMIT":
                output.append(store.commit())
            elif command == "ROLLBACK":
                output.append(store.rollback())
        except IndexError:
            # Handle malformed commands gracefully if necessary, though input is assumed clean
            pass

    return output

if __name__ == '__main__':
    # Example Usage (for testing purposes)
    program1 = """
SET A 10
BEGIN
SET B 20
GET A
COMMIT
GET B
ROLLBACK
"""
    print("--- Test Case 1 ---")
    results1 = run(program1)
    print(f"Output: {results1}") # Expected: ['10', '20']

    # Example Usage (Nested Transactions)
    program2 = """
SET X initial
BEGIN
SET Y inner_start
BEGIN
SET Z deepest
GET Z
COMMIT
GET Y
ROLLBACK
COMMIT
"""
    print("\n--- Test Case 2 ---")
    results2 = run(program2)
    # Expected: ['deepest', 'inner_start'] (Z is visible in the innermost scope, then Y after inner commit)
    print(f"Output: {results2}")

    # Example Usage (NO TRANSACTION handling)
    program3 = """
COMMIT
ROLLBACK
BEGIN
COMMIT
COMMIT
"""
    print("\n--- Test Case 3 ---")
    results3 = run(program3)
    # Expected: ['NO TRANSACTION', 'NO TRANSACTION']
    print(f"Output: {results3}")
