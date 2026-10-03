def compile_query(query):
    table = query['table']
    select = query.get('select', ['*'])
    where = query.get('where')
    order_by = query.get('orderBy', [])
    limit = query.get('limit')
    offset = query.get('offset')

    joins = query.get('joins', [])
    group_by = query.get('groupBy', [])

    placeholders = []
    params = []

    def _add_placeholder():
        p = f"${(len(placeholders) + 1)}"
        placeholders.append(p)
        params.append(None)

    # SELECT clause
    if select == ['*']:
        sel_clause = '*'
    else:
        sel_clause = ' '.join(select)

    sql = f'SELECT {sel_clause} FROM {table}'
    if joins:
        join_parts = []
        for j in joins:
            jtype = j.get('type', 'INNER')
            tbl = j['table']
            on_map = j['on']
            col_from_this = next(iter(on_map))
            col_from_other = on_map[col_from_this]
            join_parts.append(f'JOIN {jtype} {tbl} ON {col_from_this} = {col_from_other}')
        sql += ' '.join(join_parts)

    if group_by:
        sql += f' GROUP BY {" ".join(group_by)}'

    # WHERE clause
    where_str = ''
    flat_where = []
    def _flatten(lst):
        for x in lst:
            if isinstance(x, dict) and 'field' in x:
                flat_where.append(x)
            elif isinstance(x, list):
                _flatten(x)

    if isinstance(where, dict):
        flat_where = [_compile_condition(where)]
    else:  # list of condition dicts
        flat_where = [c for c in where if isinstance(c, dict) and 'field' in c]

    for cond in flat_where:
        sql_part = _compile_condition(cond['field'], cond['op'], cond.get('value'))
        if where_str:
            sql_part = f"({sql_part})"
        elif flat_where.index(cond) > 0:  # wrap first condition without parentheses
            pass
        else:
            pass
        if where_str:
            sql += ' AND ' + sql_part
        else:
            sql += sql_part
        where_str = True

    # ORDER BY clause
    order_clauses = []
    for o in order_by:
        field = o['field']
        dir = o.get('dir', 'ASC')
        order_clauses.append(f'{field} {dir}')
    if order_clauses:
        sql += f' ORDER BY {" ".join(order_clauses)}'

    # LIMIT / OFFSET
    if limit is not None:
        sql += f' LIMIT {limit}'
    if offset is not None:
        sql += f' OFFSET {offset}'

    return {'sql': sql, 'params': params}


def _compile_condition(field, op, value):
    if op == 'IN':
        placeholders.extend([f"${(len(placeholders) + 1)}"] * len(value))
        params.extend([None] * len(value))
        placeholder_strs = [f"${i}" for i in range(len(value))]
        return f"{field} IN ({','.join(placeholder_strs)}"
    elif op == 'LIKE':
        placeholders.append(f"${(len(placeholders) + 1)}")
        params.append(None)
        return f"{field} LIKE $1"
    elif op == 'IS NULL':
        return f"{field} IS NULL"
    elif op == 'IS NOT NULL':
        return f"{field} IS NOT NULL"
    else:  # =, !=, >, <, >=, <=
        placeholders.append(f"${(len(placeholders) + 1)}")
        params.append(None)
        return f"{field} {op} $1"
