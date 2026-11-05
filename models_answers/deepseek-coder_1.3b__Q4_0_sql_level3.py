import sqlparse

def compile_query(query):
    select_columns = ', '.join(query.get('select', ['*']))
    where_condition = sqlparse.sql.Statement(compile_condition(query.get('where', {})))
    having_condition = sqlparse.sql.Statement(compile_condition(query.get('having', {}))) if query.get('having', {}) else None
    subquery = query.get('subquery', None)
    order_by = ', '.join([f'{column} {direction}' for column, direction in query.get('orderBy', [])])
    limit = query.get('limit', None)
    offset = query.get('offset', None)

    sql = f"SELECT {select_columns} FROM {query['table']} WHERE {where_condition} {'HAVING' if having_condition else ''} {having_condition} {'SUBQUERY' if subquery else ''} {subquery}"

    if order_by:
        sql += f" ORDER BY {order_by}"
    if limit:
        sql += f" LIMIT {limit}"
    if offset:
        sql += f" OFFSET {offset}"

    return {'sql': sql, 'params': list(where_condition.tokens(sqlparse.sql.Identifier))}

def compile_condition(condition, parent=None):
    if isinstance(condition, dict):
        for k, v in condition.items():
            if k in ['AND', 'OR']:
                return f'({compile_condition(v, parent)})'
            else:
                if parent and k in ['>', '<', '>=', '<=']:
                    return f'{parent} {k} {condition[k]}'
                else:
                    return f'{sqlparse.sql.Identifier(k)} {condition[k]}'
    else:
        return condition
