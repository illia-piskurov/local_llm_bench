# Пример 1:
{'sql': 'SELECT name, age FROM users WHERE age = $1', 'params': [25]}

# Пример 2:
{'sql': 'SELECT name FROM users WHERE (age > $1) AND ((status = $2 OR status != $3))', 'params': [18, 'active', 'inactive']}

# Пример 3:
{'sql': 'SELECT order_id FROM orders WHERE status = $1 ORDER BY created_at DESC LIMIT 10 OFFSET 20', 'params': ['completed']}

# Пример 4:
{'sql': 'SELECT u.name FROM users JOIN orders ON user_id = user_id WHERE age > $1', 'params': [18]}
