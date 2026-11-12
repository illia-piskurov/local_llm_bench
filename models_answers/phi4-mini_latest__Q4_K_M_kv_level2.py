def run(program: str) -> list[str]:
    commands = program.strip().split('\n')
    storage = {}
    transaction_stack = []
    outputs = []
    watches = {}

    def get_current_value(key):
        if key in watches:
            return watches[key]
        return storage.get(key, "NULL")

    def set_watch(key, value):
        if key not in watches:
            watches[key] = value
        else:
            current_value = watches[key]
            if current_value != value:
                outputs.append(f"WATCH {key} {current_value} -> {value}")

    for command in commands:
        if not command.strip():
            continue
        parts = command.split()
        cmd = parts[0]

        if cmd == "SET":
            key, value = parts[1], parts[2]
            if transaction_stack:
                transaction_stack[-1][1][key] = value
                set_watch(key, value)
            else:
                storage[key] = value
        elif cmd == "GET":
            key = parts[1]
            outputs.append(str(get_current_value(key))
        elif cmd == "DELETE":
            key = parts[1]
            if transaction_stack:
                transaction_stack[-1][1].pop(key, None)
                set_watch(key, get_current_value(key))
            else:
                storage.pop(key, None)
        elif cmd == "BEGIN":
            transaction_stack.append([storage.copy(), {}])
        elif cmd == "COMMIT":
            if not transaction_stack:
                outputs.append("NO TRANSACTION")
            else:
                transaction_stack[-1][1].update(storage)
                storage = transaction_stack[-1][0]
                transaction_stack.pop()
        elif cmd == "ROLLBACK":
            if not transaction_stack:
                outputs.append("NO TRANSACTION")
            else:
                storage, _ = transaction_stack.pop()
        elif cmd == "COUNT":
            value = parts[1]
            count = sum(1 for key in storage if storage.get(key) == value)
            outputs.append(str(count))
        elif cmd == "WATCH":
            key = parts[1]
            set_watch(key, get_current_value(key))

    return outputs

# Example usage:
# program = """SET a 10
# GET a
# BEGIN
# SET a 20
# GET a
# COMMIT
# GET a
# ROLLBACK
# GET a
# COUNT 10
# WATCH a
# SET a 20
# GET a
# WATCH a
# DELETE a
# GET a
# WATCH a
"""
# print(run(program))
