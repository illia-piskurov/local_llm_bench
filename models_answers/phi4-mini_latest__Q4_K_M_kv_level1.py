def run(program: str) -> list[str]:
    commands = program.strip().split('\n')
    storage = {}
    transaction_stack = []
    outputs = []

    for command in commands:
        if not command.strip():
            continue
        parts = command.split()
        cmd = parts[0]

        if cmd == "SET":
            key, value = parts[1], parts[2]
            if transaction_stack:
                transaction_stack[-1][1][key] = value
            else:
                storage[key] = value
        elif cmd == "GET":
            key = parts[1]
            outputs.append(storage.get(key, "NULL"))
        elif cmd == "DELETE":
            key = parts[1]
            if transaction_stack:
                transaction_stack[-1][1].pop(key, None)
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
# GET a"""
# print(run(program))
