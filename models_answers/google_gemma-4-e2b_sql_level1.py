import re

def _compile_condition(cond, params):
    """Recursively compiles a single condition into an SQL segment and collects parameters."""
    if 'field' not in cond:
        raise ValueError("Invalid condition structure.")

    field = cond['field']
    op = cond['op']
    value = cond['value']

    # Ensure value is handled correctly for SQL insertion (simple conversion for demonstration)
    sql_value = str(value)

    # Generate placeholder and store value
    placeholder = f"${len(params) + 1}"
    params.append(value)

    # Build the comparison segment
    return f"{field} {op} {placeholder}"

def _compile_where(condition, params):
    """Recursively compiles a WHERE clause tree."""
    if 'AND' in condition:
        parts = [_compile_where(c, params) for c in condition['AND']]
        return f"({ ' AND '.join(parts) })"

    elif 'OR' in condition:
        parts = [_compile_where(c, params) for c in condition['OR']]
        return f"({ ' OR '.join(parts) })"

    else:
        # Atomic condition
        return _compile_condition(condition, params)

def compile_query(query: dict) -> dict:
    """
    Compiles a structured query AST into a parameterized SQL string and parameters.

    Args:
        query: Dictionary representing the query AST.

    Returns:
        A dictionary containing "sql" (string) and "params" (list of values).
    """
    
    # --- 1. Build SELECT clause ---
    select_cols = query.get('select', ['*'])
    select_str = ", ".join(select_cols)

    # --- 2. Build WHERE clause and collect parameters ---
    where_sql = ""
    params = []

    if 'where' in query:
        try:
            where_sql = _compile_where(query['where'], params)
        except Exception as e:
            raise ValueError(f"Error compiling WHERE clause: {e}")

    # --- 3. Build ORDER BY clause ---
    order_by_parts = []
    if 'orderBy' in query:
        for item in query['orderBy']:
            field = item['field']
            direction = item.get('dir', 'ASC').upper()
            order_by_parts.append(f"{field} {direction}")

    orderBy_str = ""
    if order_by_parts:
        orderBy_str = ", ".join(order_by_parts)

    # --- 4. Build LIMIT/OFFSET clause ---
    limit_str = ""
    offset_str = ""
    if 'limit' in query and isinstance(query['limit'], int):
        limit_str = f"LIMIT {query['limit']}"
    if 'offset' in query and isinstance(query['offset'], int):
        offset_str = f"OFFSET {query['offset']}"

    # --- 5. Assemble Final SQL Query ---
    base_query = f"SELECT {select_str} FROM {query['table']}"
    
    where_clause = ""
    if where_sql:
        where_clause = f"WHERE {where_sql}"

    query_parts = [
        base_query,
        where_clause,
        orderBy_str,
        limit_str,
        offset_str
    ]

    compiled_sql = " ".join([part for part in query_parts if part])
    
    return {
        "sql": compiled_sql.strip(),
        "params": params
    }

if __name__ == '__main__':
    # Example 1: Simple AND condition
    query1 = {
        'table': 'products',
        'select': ['name', 'price'],
        'where': {
            'AND': [
                {'field': 'category', 'op': '=', 'value': 'Electronics'},
                {'field': 'price', 'op': '>', 'value': 100}
            ]
        },
        'orderBy': [
            {'field': 'price', 'dir': 'DESC'}
        ],
        'limit': 10
    }

    result1 = compile_query(query1)
    print("--- Example 1 ---")
    print(f"SQL: {result1['sql']}")
    print(f"Params: {result1['params']}\n")
    # Expected SQL structure (approximation): SELECT name, price FROM products WHERE (category = $1 AND price > $2) ORDER BY price DESC LIMIT 10

    # Example 2: OR condition with nesting
    query2 = {
        'table': 'users',
        'select': ['id'],
        'where': {
            'OR': [
                {'field': 'status', 'op': '=', 'value': 0},
                {'AND': [
                    {'field': 'role', 'op': '=', 'value': 'ADMIN'},
                    {'field': 'is_active', 'op': '=', 'value': True}
                ]}
            ]
        }
    }

    result2 = compile_query(query2)
    print("--- Example 2 ---")
    print(f"SQL: {result2['sql']}")
    print(f"Params: {result2['params']}\n")
    # Expected SQL structure (approximation): SELECT id FROM users WHERE (status = $1 OR (role = $2 AND is_active = $3))

    # Example 3: Complex nested structure
    query3 = {
        'table': 'logs',
        'select': ['message'],
        'where': {
            'AND': [
                {'field': 'level', 'op': '!=', 'value': 'ERROR'},
                {'OR': [
                    {'field': 'timestamp', 'op': '<', 'value': 1678886400},
                    {'field': 'code', 'op': '=', 'value': 5}
                ]}
            ]
        },
    }

    result3 = compile_query(query3)
    print("--- Example 3 ---")
    print(f"SQL: {result3['sql']}")
    print(f"Params: {result3['params']}\n")
