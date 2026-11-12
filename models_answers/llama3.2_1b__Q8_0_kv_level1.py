def run(program: str) -> list[str]:
    transactions = []
    current_transaction = None
    for line in program.splitlines():
        if line.strip() == 'BEGIN':
            if current_transaction:
                transactions.append('COMMIT')
            current_transaction = 'nested'
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
                transactions.append(line.strip())
            else:
                transactions.append('NO TRANSACTION')
        elif line.strip() == 'GET':
            if current_transaction == 'nested':
                transactions.append(line.strip())
            else:
                transactions.append('NO TRANSACTION')
    if current_transaction == 'nested':
        transactions.append('NO TRANSACTION')
    return transactions
