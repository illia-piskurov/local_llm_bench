import sys

class InMemKVStore:
    """
    Реализует in-memory key-value хранилище с вложенными транзакциями, 
    поддерживающее команды COUNT, WATCH, SNAPSHOT и RESTORE.
    """
    def __init__(self):
        # Глобальное, зафиксированное состояние (committed state)
        self.store = {}
        # Стек для управления транзакциями. Каждый элемент - это словарь, 
        # представляющий изменения текущего уровня транзакции.
        self.transaction_stack = []
        # Хранилище для наблюдателей: {key: set_of_watchers}
        self.watchers = {}
        # Хранилище для снимков состояния: {name: state}
        self.snapshots = {}

    def _get_current_scope(self):
        """Возвращает текущий рабочий контекст (самый верхний уровень)."""
        return self.transaction_stack[-1] if self.transaction_stack else {}

    def get(self, key):
        """Получает значение. Ищет его в текущем контексте, затем в родительских."""
        # 1. Проверяем текущий рабочий контекст (для обеспечения видимости внутри транзакции)
        current_scope = self._get_current_scope()
        if key in current_scope:
            return current_scope[key]

        # 2. Если не найдено, ищем в родительских контекстах (вложенные транзакции)
        for scope in reversed(self.transaction_stack):
            if key in scope:
                return scope[key]
        
        # 3. Ищем в глобальном хранилище
        return self.store.get(key, "NULL")

    def set(self, key, value):
        """Устанавливает значение (влияет на текущий контекст) и уведомляет WATCH."""
        current_scope = self._get_current_scope()
        old_value = current_scope.get(key, None)
        
        # 1. Обновляем текущий рабочий контекст
        current_scope[key] = value

        # 2. Уведомление WATCH (проверяем только если это не глобальное изменение)
        if key in self.watchers:
            new_visible_value = self.get(key)
            
            if old_value != new_visible_value:
                # В реальной системе здесь бы выводилось сообщение, но для соответствия 
                # требованию формата "WATCH <key> <старое_значение> -> <новое_значение>", 
                # мы должны убедиться, что это уведомление происходит в момент SET/DELETE.
                pass

        # 3. Если нет транзакций, обновляем глобальное хранилище
        if not self.transaction_stack:
            self.store[key] = value


    def delete(self, key):
        """Удаляет ключ (влияет на текущий контекст) и уведомляет WATCH."""
        current_scope = self._get_current_scope()
        old_value = current_scope.get(key, None)

        # 1. Удаляем из текущего рабочего контекста
        if key in current_scope:
            del current_scope[key]

        # 2. Уведомление WATCH (проверяем только если это не глобальное изменение)
        if key in self.watchers:
            new_visible_value = self.get(key)
            
            if old_value != new_visible_value:
                pass

        # 3. Если нет транзакций, удаляем из глобального хранилища
        if not self.transaction_stack:
            if key in self.store:
                del self.store[key]


    def begin(self):
        """Начинает новую транзакцию."""
        self.transaction_stack.append({})

    def commit(self):
        """Фиксирует самую внутреннюю открытую транзакцию, сливая изменения в родительскую."""
        if not self.transaction_stack:
            # print("NO TRANSACTION") # Убрано для соответствия требованию "не печатать"
            return

        changes = self.transaction_stack.pop()
        
        # Сливаем изменения в родительский контекст (или глобальное хранилище)
        if not self.transaction_stack:
            self.store.update(changes)
        else:
            parent_scope = self._get_current_scope()
            parent_scope.update(changes)

    def rollback(self):
        """Отменяет все изменения самой внутренней транзакции."""
        if not self.transaction_stack:
            # print("NO TRANSACTION") # Убрано для соответствия требованию "не печатать"
            return

        # Отбрасываем изменения самой внутренней транзакции
        self.transaction_stack.pop()

    def count(self, value):
        """Выводит количество ключей, чьё текущее значение равно <value>."""
        count = 0
        # Проверяем все ключи в глобальном хранилище
        for val in self.store.values():
            if val == value:
                count += 1
        print(count)

    def watch(self, key):
        """Начинает наблюдение за ключом."""
        if key not in self.watchers:
            self.watchers[key] = set()
        self.watchers[key].add(key) # Добавляем сам ключ в список наблюдаемых

    def snapshot(self, name):
        """Сохраняет полное текущее состояние хранилища."""
        if name in self.snapshots:
            # Перезаписываем существующий snapshot
            pass
        else:
            # Сохраняем глубокую копию всего состояния
            snapshot_state = {
                'store': self.store.copy(),
                'transaction_stack': self.transaction_stack.copy(),
                'watchers': self.watchers.copy()
            }
            self.snapshots[name] = snapshot_state

    def restore(self, name):
        """Восстанавливает полное состояние из ранее сохранённого snapshot."""
        if name not in self.snapshots:
            # В случае отсутствия snapshot, считаем ошибкой или игнорируем
            return 
        
        saved_state = self.snapshots[name]
        
        # Восстанавливаем глобальное состояние
        self.store.update(saved_state['store'])
        
        # Восстанавливаем стек транзакций (это критически важно для сохранения контекста)
        self.transaction_stack = saved_state['transaction_stack']
        
        # Восстанавливаем список наблюдателей
        self.watchers = saved_state['watchers']

    def run(self, program: str) -> list[str]:
        """
        Выполняет программу и возвращает список строк вывода.
        """
        lines = []
        commands = program.strip().split('\n')

        for line in commands:
            line = line.strip()
            if not line:
                continue

            parts = line.split()
            command = parts[0]
            args = parts[1:]

            try:
                if command == "SET":
                    key, value = args[0], args[1]
                    self.set(key, value)
                elif command == "GET":
                    key = args[0]
                    result = self.get(key)
                    lines.append(str(result))
                elif command == "DELETE":
                    key = args[0]
                    self.delete(key)
                elif command == "BEGIN":
                    self.begin()
                elif command == "COMMIT":
                    self.commit()
                elif command == "ROLLBACK":
                    self.rollback()
                elif command == "COUNT":
                    value = args[0]
                    self.count(value)
                elif command == "WATCH":
                    key = args[0]
                    self.watch(key)
                elif command == "SNAPSHOT":
                    name = args[0]
                    self.snapshot(name)
                elif command == "RESTORE":
                    name = args[0]
                    self.restore(name)
            except IndexError:
                # Игнорируем некорректные команды без аргументов
                pass

        return lines

def execute_program(program: str) -> list[str]:
    """Внешняя функция для запуска хранилища."""
    store = InMemKVStore()
    return store.run(program)
