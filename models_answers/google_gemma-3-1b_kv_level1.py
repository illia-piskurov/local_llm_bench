import threading

class InMemoryKeyValueStore:
    def __init__(self):
        self.lock = threading.Lock()
        self.transactions = []

    def set(self, key, value):
        with self.lock:
            if not isinstance(key, str) or not isinstance(value, str):
                print("Invalid input")
                return

            try:
                self.transactions.append((key, value))
            except Exception as e:
                print(f"Error setting key: {e}")
                return

    def get(self, key):
        with self.lock:
            if not isinstance(key, str) or key is None:
                print("Invalid input")
                return "NULL"
            try:
                return self.transactions[key]
            except IndexError:
                print("No transaction")
                return "NO TRANSACTION"

    def delete(self, key):
        with self.lock:
            if not isinstance(key, str) or key is None:
                print("Invalid input")
                return

            try:
                del self.transactions[key]
            except KeyError:
                pass  # Key doesn't exist, no error

    def run(self):
        print("Starting transaction...")
        while True:
            command = input()
            if command == "SET":
                try:
                    key, value = command.split()
                    self.set(key, value)
                except ValueError:
                    print("Invalid command")

            elif command == "GET":
                value = self.get(command)
                print(value)

            elif command == "COMMIT":
                if len(self.transactions) > 0:
                    try:
                        self.transactions[-1]  # Last transaction
                    except IndexError:
                        pass
                    print("Transaction committed")
                else:
                    print("NO TRANSACTION")

            elif command == "ROLLBACK":
                if len(self.transactions) > 0:
                    try:
                        last_transaction = self.transactions[-1]
                        with self.lock:
                            self.transactions.pop()
                        print("Transaction rolled back")
                    except IndexError:
                        pass

                else:
                    print("NO TRANSACTION")


            else:
                print("Invalid command")

            if command == "END":
                break

        print("Transaction finished.")

if __name__ == '__main__':
    store = InMemoryKeyValueStore()
    store.run()
