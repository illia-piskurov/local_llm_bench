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

    # ---------- SELECT ----------
    sel_items = []
    for s in select:
        if isinstance(s, dict):
            expr = s['expr']
            alias = s.get('as')
            sel_items.append((expr, alias))
        else:
            sel_items.append((s, None))

    if not sel_items:
        sel_clause = '*'
    else:
        parts = []
        for expr, alias in sel_items:
            if alias:
                parts.append(f"{expr} AS {alias}")
            else:
                parts.append(expr)
        sel_clause = ', '.join(parts)

    sql = f"SELECT {sel_clause}"
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

    # ---------- WHERE + HAVING ----------
    flat_conditions = []
    if isinstance(where, dict):
        flat_conditions.append(_flatten_condition(where))
    else:  # list of condition dicts
        flat_conditions.extend([c for c in where if isinstance(c, dict) and 'field' in c])
    if isinstance(having, dict):
        flat_conditions.append(_flatten_condition(having))

    def _flatten_condition(node):
        if isinstance(node, dict):
            if node.get('query') is not None:
                # subquery condition
                flat_conditions.append({'field': node['field'], 'op': node['op'],
                                       'value': None, 'query': node['query']})
            else:
                flat_conditions.append(node)
        elif isinstance(node, list):
            for x in node:
                if isinstance(x, dict) and 'field' in x:
                    flat_conditions.append(x)

    def _compile_condition(field, op, value=None, query_dict=None):
        nonlocal placeholders, params
        if op == 'IN':
            # regular IN values
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

    where_str = ''
    for cond in flat_conditions:
        sql_part = _compile_condition(cond['field'], cond['op'],
                                      cond.get('value'), None)
        if query_dict is not None:  # subquery case
            sub_sql = f"({_compile_query(cond['query'])['sql']})"
            placeholder_strs = [f"${i}" for i in range(len(cond['query']['params']))]
            sql_part = f"{field} IN ({','.join(placeholder_strs)})"
        else:
            if where_str:
                sql_part = f"({sql_part})"
            elif flat_conditions.index(cond) > 0:  # wrap first condition without parentheses
                pass
            else:
                pass
        if where_str:
            sql += ' AND ' + sql_part
        else:
            sql += sql_part
        where_str = True

    # ---------- HAVING ----------
    having_clause = ''
    for cond in flat_conditions[len(where):]:
        sql_part = _compile_condition(cond['field'], cond['op'],
                                      cond.get('value'), None)
        if query_dict is not None:  # subquery case
            sub_sql = f"({_compile_query(cond['query'])['sql']})"
            placeholder_strs = [f"${i}" for i in range(len(cond['query']['params']))]
            sql_part = f"{field} IN ({','.join(placeholder_strs)})"
        else:
            if having_clause:
                sql_part = f"({sql_part})"
            elif flat_conditions.index(cond) > len(where):
                pass
            else:
                pass
        if having_clause:
            having_clause += ' AND ' + sql_part
        else:
            having_clause = sql_part
    if having_clause:
        sql += f' HAVING {having_clause}'

    # ---------- ORDER BY ----------
    order_clauses = []
    for o in order_by:
        field = o['field']
        dir = o.get('dir', 'ASC')
        order_clauses.append(f'{field} {dir}')
    if order_clauses:
        sql += f' ORDER BY {" ".join(order_clauses)}'

    # ---------- LIMIT / OFFSET ----------
    if limit is not None:
        sql += f' LIMIT {limit}'
    if offset is not None:
        sql += f' OFFSET {offset}'

    return {'sql': sql, 'params': params}


def _compile_condition(field, op, value=None, query_dict=None):
    nonlocal placeholders, params
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
    else:
        placeholders.append(f"${(len(placeholders) + 1)}")
        params.append(None)
        return f"{field} {op} $1"


def _compile_query(q):
    # recursive call for subqueries
    return compile_query(q)


# Helper to flatten condition dicts (used in where/having processing)
def _flatten_condition(node):
    if isinstance(node, dict):
        if node.get('query') is not None:
            flat_conditions.append({'field': node['field'], 'op': node['op'],
                                   'value': None, 'query': node['query']})
        else:
            flat_conditions.append(node)
    elif isinstance(node, list):
        for x in node:
            if isinstance(x, dict) and 'field' in x:
                flat_conditions.append(x)

# Subquery handling inside _compile_condition already uses compile_query recursively
