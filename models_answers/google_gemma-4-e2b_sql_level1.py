import re
from typing import Dict, List, Any

def compile_query(query: Dict[str, Any]) -> Dict[str, Any]:
    """
    Компилирует AST-дерево запроса в параметризованный SQL и список параметров.

    Args:
        query: Словарь с компонентами запроса (table, select, where, orderBy, limit, offset).

    Returns:
        Словарь с результатом {"sql": str, "params": list}.
    """
    
    # 1. SELECT Clause
    select_fields = query.get('select', ['*'])
    select_str = ", ".join(select_fields)

    # 2. FROM Clause
    table_name = query.get('table', '')
    if not table_name:
        raise ValueError("Table name is required.")
    sql_parts = [f"SELECT {select_str} FROM {table_name}"]

    # 3. WHERE Clause Processing (Recursive)
    params = []

    def process_conditions(conditions: List[Dict[str, Any]], param_index: int):
        """Рекурсивно обрабатывает список условий и собирает параметры."""
        nonlocal params
        
        if not conditions:
            return

        # Handle AND/OR grouping
        if 'AND' in conditions or 'OR' in conditions:
            operator = 'AND' if 'AND' in conditions else 'OR'
            sub_conditions = conditions[operator]
            
            # Recursively process sub-conditions
            for cond in sub_conditions:
                process_conditions(cond, param_index)
            return

        # Handle simple conditions (Base case)
        for cond in conditions:
            if 'field' not in cond or 'op' not in cond or 'value' not in cond:
                continue

            field = cond['field']
            op = cond['op']
            value = cond['value']
            
            # Determine the correct SQL operator and parameter index
            sql_op = ''
            if op == '=': sql_op = '='
            elif op == '!=': sql_op = '!='
            elif op == '>': sql_op = '>'
            elif op == '<': sql_op = '<'
            elif op == '>=': sql_op = '>='
            elif op == '<=': sql_op = '<='
            else:
                raise ValueError(f"Unsupported operator: {op}")

            # Append condition to SQL
            sql_parts.append(f"{field} {sql_op} ${param_index + 1}")
            
            # Collect parameter value
            params.append(value)
            param_index += 1


    where_conditions = query.get('where')
    if where_conditions:
        # If 'where' is a single condition, treat it as a list of one condition
        if isinstance(where_conditions, dict):
            process_conditions([where_conditions], 0)
        # If 'where' is already a list of conditions (less likely based on prompt structure, but safe check)
        elif isinstance(where_conditions, list):
             for i, cond in enumerate(where_conditions):
                 if 'field' in cond and 'op' in cond and 'value' in cond:
                     sql_parts.append(f"{cond['field']} {cond['op']} ${i + 1}")
                     params.append(cond['value'])


    # 4. ORDER BY Clause
    order_by_fields = []
    if query.get('orderBy'):
        for item in query['orderBy']:
            field = item.get('field')
            direction = item.get('dir', 'ASC').upper()
            if field:
                order_by_fields.append(f"{field} {direction}")

    if order_by_fields:
        sql_parts.append("ORDER BY " + ", ".join(order_by_fields))

    # 5. LIMIT and OFFSET Clause
    limit = query.get('limit')
    offset = query.get('offset')

    if limit is not None:
        sql_parts.append(f"LIMIT {limit}")
    
    if offset is not None:
        sql_parts.append(f"OFFSET {offset}")

    # Final Assembly
    final_sql = " ".join(sql_parts) + ";" # Ensure termination, though LIMIT/OFFSET often stand alone

    return {"sql": final_sql, "params": params}

if __name__ == '__main__':
    # Пример 1: Простой запрос
    query1 = {
        'table': 'users',
        'select': ['id', 'name'],
        'where': {
            'field': 'status',
            'op': '=',
            'value': 'active'
        },
        'orderBy': [{'field': 'name', 'dir': 'ASC'}],
        'limit': 10
    }

    result1 = compile_query(query1)
    print("--- Пример 1 ---")
    print(f"SQL: {result1['sql']}")
    print(f"Params: {result1['params']}\n")
    # Ожидаемый результат: SQL: SELECT id, name FROM users WHERE status = $1 ORDER BY name ASC LIMIT 10, Params: ['active']

    # Пример 2: Сложный запрос с вложенными условиями (AND/OR)
    query2 = {
        'table': 'products',
        'select': ['name', 'price'],
        'where': {
            'AND': [
                {'field': 'category', 'op': '=', 'value': 'electronics'},
                {
                    'OR': [
                        {'field': 'price', 'op': '>', 'value': 100},
                        {'field': 'stock', 'op': '<', 'value': 5}
                    ]
                }
            ]
        },
        'orderBy': [{'field': 'price', 'dir': 'DESC'}],
        'offset': 20
    }

    result2 = compile_query(query2)
    print("--- Пример 2 ---")
    print(f"SQL: {result2['sql']}")
    print(f"Params: {result2['params']}\n")
    # Ожидаемый результат (примерно): SQL: SELECT name, price FROM products WHERE category = $1 AND (price > $2 OR stock < $3) ORDER BY price DESC OFFSET 20, Params: ['electronics', '100', '5']
