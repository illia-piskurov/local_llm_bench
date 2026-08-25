class TransactionDB:
    def __init__(self):
        self.global_store = {}
        self.stack = []  # Stack of nested transactions

    def run(self, program: str) -> list[str]:
        output = []
        commands = [cmd.strip() for cmd in program.split('\n') if cmd.strip()]
        current_transaction = None
        transaction_stack = []

        for cmd in commands:
            parts = cmd.split()
            if not parts:
                continue

            if parts[0] == 'BEGIN':
                # Start a new nested transaction
                new_tx = {'store': {}, 'parent': current_transaction}
                transaction_stack.append(new_tx)
                current_transaction = new_tx

            elif parts[0] == 'COMMIT':
                if not transaction_stack:
                    output.append("NO TRANSACTION")
                    continue

                # Commit the innermost transaction
                tx = transaction_stack.pop()
                if tx['parent'] is None:  # Global commit
                    self.global_store.update(tx['store'])
                else:
                    tx['parent']['store'].update(tx['store'])

            elif parts[0] == 'ROLLBACK':
                if not transaction_stack:
                    output.append("NO TRANSACTION")
                    continue

                # Rollback the innermost transaction
                tx = transaction_stack.pop()
                # Clear the transaction store (changes are undone)
                tx['store'] = {}

            elif parts[0] == 'SET' and len(parts) >= 3:
                key, value = parts[1], parts[2]
                current_tx = transaction_stack[-1] if transaction_stack else self.global_store
                current_tx[key] = value

            elif parts[0] == 'GET':
                key = parts[1]
                # Find the most recent active transaction that contains this key
                tx = None
                for t in reversed(transaction_stack):
                    if key in t['store']:
                        tx = t
                        break
                if tx:
                    output.append(tx['store'].get(key, "NULL"))
                elif key in self.global_store:
                    output.append(self.global_store.get(key, "NULL"))
                else:
                    output.append("NULL")

            elif parts[0] == 'DELETE' and len(parts) >= 2:
                key = parts[1]
                # Delete from the most recent active transaction first
                for t in reversed(transaction_stack):
                    if key in t['store']:
                        del t['store'][key]
                        break
                elif key in self.global_store:
                    del self.global_store[key]

        return output

# Example usage (for testing):
db = TransactionDB()
program = """
BEGIN
SET a 10
GET a
COMMIT
GET a
"""
print(db.run(program))
