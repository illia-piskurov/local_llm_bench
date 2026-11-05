import sqlparse

def compile_query(query):
    table = query.get('table', '')
    select_columns = ','.join(query.get('select', ['*']))
    where_condition = sqlparse.sql.Statement(compile_condition(query.get('where', {})))
    order_by = ','.join([f'{field} {direction}' for field, direction in query.get('orderBy', [])])
    limit = query.get('limit', None)
    offset = query.get('offset', None)

    sql = f"SELECT {select_columns} FROM {table} WHERE {where_condition} ORDER BY {order_by} {'LIMIT' if limit else ''} {limit} {'OFFSET' if offset else ''} {offset}"

    return {'sql': sql, 'params': list(where_condition.tokens(sqlparse.sql.Identifier))}

def compile_condition(condition, parent=None):
    if isinstance(condition, dict):
        for k, v in condition.items():
            if k in ['AND', 'OR']:
                return f'({compile_condition(condition[k], parent)})'
            else:
                if parent and k in ['>', '<', '>=', '<=']:
                    return f'{parent} {k} {condition[k]}'
                else:
                    return f'{sqlparse.sql.Identifier(k)} {condition[k]}'
    else:
        return condition
