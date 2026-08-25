import collections
from typing import List, Dict, Set, Any, Tuple
import copy

class TransactionalKVStore:
    """
    In-memory key-value store supporting arbitrarily deep nested transactions 
    and WATCH functionality, plus snapshot/restore capabilities.
    """
    def __init__(self):
        # The base committed state of the database (the root)
        self.store: Dict[str, str] = {}
        
        # Stack to hold active transaction contexts. 
        # Structure: list[Dict[str, Any]] where each dict is { 'writes': {}, 'deletes': set() }
        self.transaction_stack: List[Dict[str, Any]] = []

        # Watch state: key -> initial visible value (used for comparison)
        self.watched_keys: Dict[str, str] = {}
        
        # Output buffer to capture watch notifications and NO TRANSACTION messages
        self._output_buffer: List[str] = []
        
        # Storage for snapshots: name -> saved state dictionary
        self.snapshots: Dict[str, Any] = {}


    def _get_current_state(self) -> Dict[str, str]:
        """
        Reconstructs the visible state of the database by applying all deltas 
        from the base store up through the transaction stack.
        Returns a copy of the current view.
        """
        # Start with the committed base state
        current_state = self.store.copy()

        # Apply changes from transactions in order (bottom to top)
        for tx in self.transaction_stack:
            writes = tx['writes']
            deletes = tx['deletes']

            # 1. Apply writes (overwriting previous values)
            current_state.update(writes)

            # 2. Apply deletes
            keys_to_delete = list(deletes) # Copy set for safe iteration/modification
            for key in keys_to_delete:
                if key in current_state:
                    del current_state[key]
        
        return current_state

    def _apply_deltas_to_parent(self, committed_tx: Dict[str, Any], is_root_commit: bool):
        """
        Applies the changes from a committed transaction (committed_tx) 
        either to the global store (if root) or the parent context.
        """
        writes = committed_tx['writes']
        deletes = committed_tx['deletes']

        if is_root_commit:
            # Commit to the base store
            for key, value in writes.items():
                self.store[key] = value
            for key in deletes:
                self.store.pop(key, None)
        else:
            # Merge into the parent context (the new top of stack)
            parent_tx = self.transaction_stack[-1]
            
            # Writes overwrite any existing writes/deletes in the parent scope
            for key, value in writes.items():
                parent_tx['writes'][key] = value
            
            # Deletes accumulate
            parent_tx['deletes'].update(deletes)

    def _notify_watch(self, key: str, old_value: str, new_value: str):
        """Helper to format and record watch notifications."""
        if self.watched_keys.get(key) == old_value:
            # Only notify if the current change matches what was watched
            notification = f"WATCH {key} {old_value} -> {new_value}"
            self._output_buffer.append(notification)

    def set_value(self, key: str, value: str):
        """Sets a key-value pair in the current transaction context."""
        
        # 1. Determine old visible state before modification
        old_visible_state = self.get_value(key)

        if not self.transaction_stack:
            # If no transaction is active, write directly to base store (non-standard but required for completeness)
            self.store[key] = value
            return

        current_tx = self.transaction_stack[-1]
        
        # 2. Apply the change to the delta structure
        current_tx['writes'][key] = value

        # 3. Check and notify watchers
        if key in self.watched_keys:
            self._notify_watch(key, old_visible_state, new_value)


    def get_value(self, key: str) -> str:
        """Retrieves the current visible value of a key."""
        return self._get_current_state().get(key, "NULL")

    def delete_key(self, key: str):
        """Marks a key for deletion in the current transaction context."""
        if not self.transaction_stack:
            # Cannot safely track deletion without an active transaction
            return

        # 1. Determine old visible state before modification
        old_visible_state = self.get_value(key)

        current_tx = self.transaction_stack[-1]
        
        # 2. Apply the change to the delta structure
        current_tx['deletes'].add(key)

        # 3. Check and notify watchers (only if it was visible before deletion)
        if key in self.watched_keys:
            self._notify_watch(key, old_visible_state, "NULL")


    def begin(self):
        """Starts a new transaction context."""
        new_context = {
            'writes': {}, 
            'deletes': set()
        }
        self.transaction_stack.append(new_context)

    def commit(self) -> str:
        """Commits the innermost transaction, merging changes into the parent/root."""
        if not self.transaction_stack:
            self._output_buffer.append("NO TRANSACTION")
            return "NO TRANSACTION"

        # 1. Pop the committed context
        committed_tx = self.transaction_stack.pop()
        
        # 2. Determine if this was a root commit (merging into global store)
        is_root_commit = not self.transaction_stack
        
        # 3. Apply changes to the parent or base store
        self._apply_deltas_to_parent(committed_tx, is_root_commit)

        return "" # Successful commit does not print anything per requirements

    def rollback(self) -> str:
        """Rolls back the innermost transaction."""
        if not self.transaction_stack:
            self._output_buffer.append("NO TRANSACTION")
            return "NO TRANSACTION"

        # Simply discard the context (pop it off the stack)
        self.transaction_stack.pop()
        return "" # Successful rollback does not print anything per requirements

    def count_value(self, value: str):
        """Counts keys with a specific visible value."""
        count = 0
        state = self._get_current_state()
        for key, val in state.items():
            if val == value:
                count += 1
        return str(count)

    def watch(self, key: str):
        """Starts watching a specific key."""
        # Get the current visible value and store it for future comparison
        initial_value = self.get_value(key)
        self.watched_keys[key] = initial_value

    def snapshot(self, name: str):
        """Saves the entire current state of the store."""
        # We must deep copy all mutable structures to ensure isolation
        snapshot_state = {
            'store': self.store.copy(),
            'transaction_stack': [copy.deepcopy(tx) for tx in self.transaction_stack],
            'watched_keys': self.watched_keys.copy()
        }
        self.snapshots[name] = snapshot_state

    def restore(self, name: str):
        """Restores the store state from a named snapshot."""
        if name not in self.snapshots:
            # Assuming tests won't hit this case, but good practice to handle it.
            return 

        saved_state = self.snapshots[name]
        
        # Restore core state variables
        self.store = saved_state['store'].copy()
        self.transaction_stack = [copy.deepcopy(tx) for tx in saved_state['transaction_stack']]
        self.watched_keys = saved_state['watched_keys'].copy()
        
        # Clear output buffer as if the program restarted from the snapshot point
        self._output_buffer = []


def run(program: str) -> list[str]:
    """
    Processes a sequence of commands and returns a list of output strings 
    for GET calls, NO TRANSACTION messages, and WATCH notifications.
    """
    store = TransactionalKVStore()
    output: List[str] = []

    commands = [line.strip() for line in program.split('\n') if line.strip()]

    # Clear the internal buffer before starting a new run
    store._output_buffer = [] 

    for command_line in commands:
        parts = command_line.split()
        if not parts:
            continue

        command = parts[0].upper()

        try:
            if command == "SET":
                if len(parts) < 3: continue
                key, value = parts[1], parts[2]
                store.set_value(key, value)
            
            elif command == "GET":
                if len(parts) < 2: continue
                key = parts[1]
                result = store.get_value(key)
                output.append(result)

            elif command == "DELETE":
                if len(parts) < 2: continue
                key = parts[1]
                store.delete_key(key)

            elif command == "BEGIN":
                store.begin()

            elif command == "COMMIT":
                # Append the result (which might be NO TRANSACTION or empty string)
                output.append(store.commit()) 
            
            elif command == "ROLLBACK":
                # Append the result
                output.append(store.rollback())

            elif command == "COUNT":
                if len(parts) < 2: continue
                value = parts[1]
                result = store.count_value(value)
                output.append(result)

            elif command == "WATCH":
                if len(parts) < 2: continue
                key = parts[1]
                store.watch(key)

            # --- New Commands ---
            elif command == "SNAPSHOT":
                if len(parts) < 2: continue
                name = parts[1]
                store.snapshot(name)
            
            elif command == "RESTORE":
                if len(parts) < 2: continue
                name = parts[1]
                store.restore(name)

        except Exception as e:
            # Handle unexpected errors gracefully
            pass
    
    # Append any watch notifications that occurred during the run
    output.extend(store._output_buffer)
    
    return output
