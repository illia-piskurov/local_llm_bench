def run(program):
    lines = [line.strip() for line in program.splitlines() if line.strip()]
    storage = {}
    transactions = []
    outputs = []
    for line in lines:
        if not line:
            continue
        parts = line.split()
        if parts[0] == 'SET':
            key = parts[1]
            value = parts[2]
            transactions[-1][key] = value
        elif parts[0] == 'GET':
            key = parts[1]
            if key in storage:
                outputs.append(storage[key])
            elif transactions:
                outputs.append(transactions[-1].get(key, 'NULL'))
            else:
                outputs.append('NULL')
        elif parts[0] == 'DELETE':
            key = parts[1]
            if transactions:
                transactions[-1].pop(key, None)
        elif parts[0] == 'BEGIN':
            transactions.append({})
        elif parts[0] == 'COMMIT':
            if not transactions:
                outputs.append('NO TRANSACTION')
            else:
                parent = transactions[-2]
                for key, value in transactions[-1].items():
                    parent[key] = value
                transactions.pop()
        elif parts[0] == 'ROLLBACK':
            if not transactions:
                outputs.append('NO TRANSACTION')
            else:
                transactions.pop()
    return outputs
