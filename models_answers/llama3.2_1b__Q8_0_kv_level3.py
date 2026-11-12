def run(program: str) -> list[str]:
    transactions = []
    current_transaction = None
    snapshot_name = None
    for line in program.splitlines():
        if line.strip() == 'BEGIN':
            if current_transaction:
                transactions.append('COMMIT')
            current_transaction = 'nested'
            snapshot_name = line.strip()
        elif line.strip() == 'COMMIT':
            if current_transaction == 'nested':
                transactions.append('NO TRANSACTION')
            current_transaction = None
        elif line.strip() == 'ROLLBACK':
            if current_transaction == 'nested':
                transactions.append('NO TRANSACTION')
            current_transaction = None
        elif line.strip() == 'SET':
            if current_transaction == 'nested':
                old_value = None
                for t in transactions:
                    if t == 'COMMIT':
                        old_value = None
                        break
                    elif t == 'NO TRANSACTION':
                        old_value = None
                        break
                    elif t == 'WATCH':
                        old_value = t.split('->')[1]
                if old_value is None:
                    transactions.append('NO TRANSACTION')
                else:
                    transactions.append(f'WATCH {line.strip()} {old_value} -> {line.strip()}')
            else:
                transactions.append(line.strip())
            if line.strip() == 'NO TRANSACTION':
                current_transaction = None
        elif line.strip() == 'GET':
            if current_transaction == 'nested':
                transactions.append(line.strip())
            else:
                transactions.append('NO TRANSACTION')
        elif line.strip() == 'COUNT':
            if current_transaction == 'nested':
                transactions.append(line.strip())
            else:
                transactions.append('NO TRANSACTION')
        elif line.strip() == 'SNAPSHOT':
            if current_transaction == 'nested':
                transactions.append(f'SNAPSHOT {snapshot_name}')
            else:
                transactions.append('NO TRANSACTION')
        elif line.strip() == 'RESTORE':
            if current_transaction == 'nested':
                if snapshot_name is None:
                    transactions.append('NO TRANSACTION')
                else:
                    transactions.append(f'RESTORE {snapshot_name}')
            else:
                transactions.append(line.strip())
            if line.strip() == 'NO TRANSACTION':
                current_transaction = None
