import copy
from typing import List, Dict, Any, Optional

class KeyValueStore:
    """
    In-memory key-value store supporting nested transactions.
    """
    def __init__(self):
        # The global, committed state of the store
        self.store: Dict[str, Any] = {}
        
        # Stack to manage transaction contexts. 
        # Each context stores changes relative to its parent/global scope.
        # Structure: [{'changes': {key: value}, 'is_root': bool}]
        self.transaction_stack: List[Dict[str, Any]] = []

    def _get_current_effective_state(self) -> Dict[str, Any]:
        """
        Calculates the effective state by applying all changes from 
        the global store through the transaction stack in order.
        Returns a deep copy of the resulting dictionary.
        """
        # Start with a copy of the committed base store
        effective_state = self.store.copy()

        # Apply changes from transactions, from oldest to newest (bottom to top)
        for tx in self.transaction_stack:
            changes = tx['changes']
            
            # Apply updates and deletions
            for key, value in changes.items():
                if value is None:
                    # Deletion marker
                    effective_state[key] = None # Mark for deletion/overwriting
                else:
                    effective_state[key] = value
        
        return effective_state

    def _get_current_transaction_context(self) -> Dict[str, Any]:
        """Returns the changes dictionary of the topmost transaction."""
        if not self.transaction_stack:
            raise IndexError("No active transactions.")
        return self.transaction_stack[-1]['changes']

    def set_key(self, key: str, value: Any):
        """Sets a key-value pair in the current scope (global or transaction)."""
        if not self.transaction_stack:
            # Direct write to global store if no transactions are active
            self.store[key] = value
            return

        changes = self._get_current_transaction_context()
        changes[key] = value

    def get_key(self, key: str) -> Optional[Any]:
        """Retrieves the current effective value of a key."""
        effective_state = self._get_current_effective_state()
        
        # Check if the key exists and is not marked for deletion (None)
        if key in effective_state and effective_state[key] is not None:
            return effective_state[key]
        else:
            return None

    def delete_key(self, key: str):
        """Marks a key for deletion in the current scope."""
        # Deletion always targets the topmost transaction context
        if not self.transaction_stack:
            # If no transactions are open, we cannot 'delete' it safely 
            # without affecting other potential scopes, so we treat this as a no-op 
            # for simplicity in the global scope (or require BEGIN first).
            return

        changes = self._get_current_transaction_context()
        # Use None as a marker to signify deletion within the transaction context
        if key not in changes:
             changes[key] = None


    def begin(self):
        """Starts a new (potentially nested) transaction."""
        # Initialize a new empty change set for this scope
        new_context = {'changes': {}}
        self.transaction_stack.append(new_context)

    def commit(self) -> str:
        """Commits the innermost transaction, merging changes into the parent scope."""
        if not self.transaction_stack:
            return "NO TRANSACTION"

        # 1. Get the context to be committed (T_inner)
        committed_context = self.transaction_stack[-1]
        changes_to_commit = committed_context['changes']
        self.transaction_stack.pop() # Remove T_inner

        if not changes_to_commit:
            # Nothing changed, just pop and return success (or nothing)
            return "" 

        # 2. Determine the parent scope's change set
        parent_context = None
        if self.transaction_stack:
            parent_context = self._get_current_transaction_context()
        else:
            # If stack is empty, we commit directly to the global store (self.store)
            pass 

        # 3. Apply changes from T_inner to the parent/global scope
        if parent_context:
            parent_changes = parent_context['changes']
            for key, value in changes_to_commit.items():
                if value is None:
                    # Mark for deletion in the parent's context
                    parent_changes[key] = None 
                else:
                    # Update/set in the parent's context
                    parent_changes[key] = value
        else:
            # Commit to global store (self.store)
            for key, value in changes_to_commit.items():
                if value is None:
                    # Deletion marker for global scope
                    if key in self.store and self.store[key] is not None:
                         del self.store[key]
                else:
                    self.store[key] = value

        return "" # Successful commit produces no output string

    def rollback(self) -> str:
        """Rolls back the innermost transaction, discarding its changes."""
        if not self.transaction_stack:
            return "NO TRANSACTION"

        # Simply pop and discard the context's changes
        self.transaction_stack.pop()
        return "" # Successful rollback produces no output string


    def run(self, program: str) -> List[str]:
        """
        Executes a sequence of commands and captures required output.
        Returns a list of strings representing the output for GET or NO TRANSACTION.
        """
        lines = [line.strip() for line in program.split('\n') if line.strip()]
        output: List[str] = []

        for line in lines:
            parts = line.split()
            if not parts:
                continue

            command = parts[0].upper()
            args = parts[1:]

            try:
                if command == "SET":
                    if len(args) < 2: continue
                    key, value_str = args[0], args[1]
                    # Attempt to convert simple types (assuming strings or basic literals)
                    try:
                        value = int(value_str)
                    except ValueError:
                        try:
                            value = float(value_str)
                        except ValueError:
                            value = value_str # Default to string

                    self.set_key(key, value)
                
                elif command == "GET":
                    if not args: continue
                    key = args[0]
                    result = self.get_key(key)
                    output.append(str(result) if result is not None else "NULL")

                elif command == "DELETE":
                    if not args: continue
                    key = args[0]
                    self.delete_key(key)

                elif command == "BEGIN":
                    self.begin()

                elif command == "COMMIT":
                    result = self.commit()
                    # Commit success produces no output, only NO TRANSACTION is required
                    if result: 
                        output.append(result)

                elif command == "ROLLBACK":
                    result = self.rollback()
                    if result:
                        output.append(result)
            except Exception as e:
                # In a real system, we would log this error. Here, we just skip the line.
                pass 

        return output

# Example Usage (Not part of the final returned code block, but for testing):
# store = KeyValueStore()
# program1 = """
# SET user_id 100
# GET user_id
# BEGIN
# SET name "Alice"
# GET name
# COMMIT
# GET name
# DELETE user_id
# GET user_id
# ROLLBACK
# GET user_id
# """
# print("--- Test 1 ---")
# results = store.run(program1)
# for r in results: print(r) # Expected output: 100, Alice, NULL

# program2 = """
# BEGIN
# SET a 1
# BEGIN
# SET b 2
# GET b
# COMMIT
# GET b
# ROLLBACK
# GET b
# COMMIT
# GET a
# """
# print("\n--- Test 2 ---")
# store_nested = KeyValueStore()
# results = store_nested.run(program2)
# for r in results: print(r) # Expected output: 2, NULL (b is rolled back), 1
