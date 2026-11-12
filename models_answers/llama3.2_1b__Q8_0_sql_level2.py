import re

def compile_query(query):
    table = query.get('table', '')
    select = query.get('select', [])
    where = query.get('where', {})
    orderBy = query.get('orderBy', [])
    limit = query.get('limit', 0)
    offset = query.get('offset', 0)

    params = []
    sql = 'SELECT '
    if select:
        sql += ', '.join(select)
    sql += ' FROM ' + table

    if where:
        placeholders = []
        for field, op, value in where.items():
            if isinstance(value, dict):
                placeholders.extend(re.findall(r'\$(\d+)', str(value)))
            else:
                placeholders.append(f'${value}')
        sql += ' WHERE '
        for field, op, value in where.items():
            if isinstance(value, dict):
                sql += f'{field} {op} {placeholders.pop(0)}'
            else:
                sql += f'{field} {op} {value}'

    if orderBy:
        sql += ' ORDER BY '
        for field, dir in orderBy:
            sql += f'{field} {dir}'

    if limit:
        sql += ' LIMIT ' + str(limit)

    if offset:
        sql += ' OFFSET ' + str(offset)

    if 'joins' in query:
        joins = query.get('joins', [])
        sql += ' JOIN '
        for join in joins:
            sql += join['type'] + ' ' + join['table'] + ' ON ' + join['on']

    if 'groupBy' in query:
        groupBy = query.get('groupBy', [])
        sql += ' GROUP BY '
        for field in groupBy:
            sql += field + ' '

    if 'op' in query:
        op = query.get('op', '')
        if op == 'IN':
            value = query.get('value', [])
            sql += ' IN (' + ', '.join(re.escape(x) for x in value) + ')'
        elif op == 'IS NULL':
            sql += ' IS NULL'
        elif op == 'IS NOT NULL':
            sql += ' IS NOT NULL'
        elif op == 'LIKE':
            value = query.get('value', [])
            sql += ' LIKE %s' % re.escape(''.join(re.escape(x) for x in value))
        else:
            raise ValueError('Unsupported operator: ' + op)

    return {'sql': sql, 'params': params}
