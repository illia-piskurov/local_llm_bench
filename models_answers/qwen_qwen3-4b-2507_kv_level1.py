class InMemoryKVStore:
    def __init__(self):
        self.data = {}
        self.transactions = []  # Stack of transactions (each is a dict of key-value pairs)

    def run(self, program: str) -> list[str]:
        output = []
        lines = [line.strip() for line in program.split('\n') if line.strip()]
        
        for line in lines:
            if not line:
                continue
                
            parts = line.split(' ', 1)
            cmd = parts[0]
            
            if cmd == "SET":
                key, value = parts[1], parts[1].split(' ', 1)[1] if len(parts) > 1 else ""
                if len(parts) > 1:
                    value = parts[1]
                if self.transactions:
                    # Current transaction is the top one
                    current_tx = self.transactions[-1]
                    current_tx[key] = value
                else:
                    self.data[key] = value
                # Output is not generated for SET
                
            elif cmd == "GET":
                key = parts[1] if len(parts) > 1 else ""
                if self.transactions:
                    current_tx = self.transactions[-1]
                    if key in current_tx:
                        output.append(str(current_tx[key]))
                    else:
                        output.append("NULL")
                else:
                    if key in self.data:
                        output.append(str(self.data[key]))
                    else:
                        output.append("NULL")
                        
            elif cmd == "DELETE":
                key = parts[1] if len(parts) >  1 else ""
                if self.transactions:
                    current_tx = self.transactions[-1]
                    if key in current_tx:
                        del current_tx[key]
                else:
                    if key in self.data:
                        del self.data[key]
                        
            elif cmd == "BEGIN":
                self.transactions.append({})
                
            elif cmd == "COMMIT":
                if not self.transactions:
                    output.append("NO TRANSACTION")
                else:
                    current_tx = self.transactions.pop()
                    if self.transactions:
                        # Merge current transaction into the parent
                        for key, value in current_tx.items():
                            self.transactions[-1][key] = value
                    else:
                        # This is the top-level transaction, merge into global data
                        for key, value in current_tx.items():
                            self.data[key] = value
                    # No output for COMMIT (only for "NO TRANSACTION")
                    
            elif cmd == "ROLLBACK":
                if not self.transactions:
                    output.append("NO TRANSACTION")
                else:
                    self.transactions.pop()
                    
        return output


def run(program: str) -> list[str]:
    store = InMemoryKVStore()
    return store.run(program)
