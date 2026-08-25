def run(program: str) -> list[str]:
    lines = program.strip().split('\n') if program else []
    output = []
    
    # Хранилище ключ-значение
    store = {}
    
    # Стек транзакций: каждая транзакция — словарь изменений и ссылка на родителя
    # Структура: {'changes': {}, 'parent': None}
    transactions = [None]  # Индекс 0 — "глобальное" состояние, но мы не используем его как транзакцию
    
    def get_current_transaction():
        """Возвращает текущую открытую транзакцию или None"""
        if len(transactions) == 1:
            return None
        return transactions[-1]
    
    def commit():
        """Зафиксировать текущую транзакцию в родительскую"""
        current = get_current_transaction()
        if current is None:
            output.append("NO TRANSACTION")
            return
        
        parent = current['parent']
        
        # Если родитель — это "глобальное" хранилище (root), то применяем изменения напрямую
        if parent is None:
            store.update(current['changes'])
        else:
            # Иначе сливаем в родительскую транзакцию
            for k, v in current['changes'].items():
                parent['changes'][k] = v
        
        # Удаляем текущую транзакцию из стека
        transactions.pop()
    
    def rollback():
        """Откатить текущую транзакцию"""
        current = get_current_transaction()
        if current is None:
            output.append("NO TRANSACTION")
            return
        
        # Удаляем изменения (не удаляем саму транзакцию, просто очищаем её changes)
        current['changes'].clear()
    
    def set_value(key, value):
        """Установить значение ключа"""
        current = get_current_transaction()
        if current is not None:
            current['changes'][key] = value
        else:
            store[key] = value
    
    def get_value(key):
        """Получить значение ключа"""
        current = get_current_transaction()
        if current is not None and key in current['changes']:
            return current['changes'][key]
        elif key in store:
            return store[key]
        else:
            output.append("NULL")
    
    def delete_key(key):
        """Удалить ключ"""
        current = get_current_transaction()
        if current is not None:
            if key in current['changes']:
                del current['changes'][key]
            elif key in store:
                del store[key]
        else:
            if key in store:
                del store[key]
    
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        
        parts = stripped.split()
        command = parts[0].upper()
        
        if command == 'SET':
            if len(parts) >= 3:
                key = parts[1]
                value = parts[2]
                set_value(key, value)
        elif command == 'GET':
            if len(parts) >= 2:
                key = parts[1]
                get_value(key)
        elif command == 'DELETE':
            if len(parts) >= 2:
                key = parts[1]
                delete_key(key)
        elif command == 'BEGIN':
            # Создаем новую транзакцию, родитель — текущая открытая или None (глобальное)
            parent = get_current_transaction()
            new_tx = {'changes': {}, 'parent': parent}
            transactions.append(new_tx)
        elif command == 'COMMIT':
            commit()
        elif command == 'ROLLBACK':
            rollback()
    
    return output
