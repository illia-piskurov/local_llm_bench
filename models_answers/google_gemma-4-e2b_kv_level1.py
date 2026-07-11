import sys

class InMemKVStore:
    """
    Реализует in-memory key-value хранилище с вложенными транзакциями.
    """
    def __init__(self):
        # Глобальное, зафиксированное состояние (committed state)
        self.store = {}
        # Стек для управления транзакциями. Каждый элемент - это словарь, 
        # представляющий изменения текущего уровня транзакции.
        self.transaction_stack = []

    def _get_current_scope(self):
        """Возвращает текущий рабочий контекст (самый верхний уровень)."""
        return self.transaction_stack[-1] if self.transaction_stack else {}

    def set_internal(self, key, value):
        """Внутренняя функция для установки значения в текущем рабочем контексте."""
        current_scope = self._get_current_scope()
        current_scope[key] = value

    def delete_internal(self, key):
        """Внутренняя функция для удаления ключа в текущем рабочем контексте."""
        current_scope = self._get_current_scope()
        if key in current_scope:
            del current_scope[key]

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
        """Устанавливает значение (влияет на текущий контекст)."""
        if not self.transaction_stack:
            # Если транзакций нет, устанавливаем напрямую в глобальное хранилище
            self.store[key] = value
        else:
            # Иначе, устанавливаем в текущий рабочий контекст
            self.set_internal(key, value)

    def delete(self, key):
        """Удаляет ключ (влияет на текущий контекст)."""
        if not self.transaction_stack:
            # Если транзакций нет, удаляем из глобального хранилища
            if key in self.store:
                del self.store[key]
        else:
            # Иначе, удаляем из текущего рабочего контекста
            self.delete_internal(key)

    def begin(self):
        """Начинает новую транзакцию."""
        self.transaction_stack.append({})

    def commit(self):
        """Фиксирует самую внутреннюю открытую транзакцию, сливая изменения в родительскую."""
        if not self.transaction_stack:
            print("NO TRANSACTION")
            return

        # Извлекаем изменения из самой внутренней транзакции
        changes = self.transaction_stack.pop()
        
        # Сливаем изменения в родительский контекст (или глобальное хранилище)
        if not self.transaction_stack:
            # Если это была самая внутренняя транзакция, сливаем в глобальное хранилище
            self.store.update(changes)
        else:
            # Иначе, сливаем в родительский контекст
            parent_scope = self._get_current_scope()
            parent_scope.update(changes)

    def rollback(self):
        """Отменяет все изменения самой внутренней транзакции."""
        if not self.transaction_stack:
            print("NO TRANSACTION")
            return

        # Отбрасываем изменения самой внутренней транзакции
        self.transaction_stack.pop()

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
            except IndexError:
                # Игнорируем некорректные команды без аргументов
                pass
            except Exception as e:
                # В реальной системе здесь должна быть более детальная обработка ошибок
                # print(f"Error executing command: {line}. Error: {e}", file=sys.stderr)
                pass

        return lines

def execute_program(program: str) -> list[str]:
    """Внешняя функция для запуска хранилища."""
    store = InMemKVStore()
    return store.run(program)

if __name__ == '__main__':
    # Пример использования:
    
    print("--- Тест 1: Базовые операции ---")
    program1 = """
SET a 10
GET a
DELETE a
GET a
"""
    results1 = execute_program(program1)
    print("\nРезультаты (Тест 1):")
    for res in results1:
        print(res)

    print("\n" + "="*30 + "\n")

    print("--- Тест 2: Вложенные транзакции и Rollback ---")
    program2 = """
SET x 100
BEGIN
SET y 200
GET x
GET y
COMMIT
"""
    results2 = execute_program(program2)
    print("\nРезультаты (Тест 2):")
    for res in results2:
        print(res)

    print("\n" + "="*30 + "\n")

    print("--- Тест 3: Вложенные транзакции и Rollback ---")
    program3 = """
SET a 10
BEGIN
SET b 20
BEGIN
SET c 30
GET a
GET b
ROLLBACK
GET c
COMMIT
"""
    results3 = execute_program(program3)
    print("\nРезультаты (Тест 3):")
    for res in results3:
        print(res)

    print("\n" + "="*30 + "\n")

    print("--- Тест 4: Rollback без изменений ---")
    program4 = """
SET a 10
BEGIN
ROLLBACK
GET a
"""
    results4 = execute_program(program4)
    print("\nРезультаты (Тест 4):")
    for res in results4:
        print(res)
