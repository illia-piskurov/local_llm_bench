def compile_query(query: dict) -> dict:
    table = query.get('table', '')
    select = query.get('select', [])
    where = query.get('where', {})
    orderBy = query.get('orderBy', [])
    limit = query.get('limit')
    offset = query.get('offset')
    joins = query.get('joins', [])
    groupBy = query.get('groupBy', [])
    having = query.get('having', None)
    subqueries = query.get('subqueries', {})

    params = []
    conditions = []
    subquery_params = []

    def add_condition(cond):
        nonlocal params
        if isinstance(cond, dict) and len(cond) == 3:
            field, op, value = cond['field'], cond['op'], cond['value']
            if op in ('IS NULL', 'IS NOT NULL'):
                conditions.append(f"{field} {op}")
            elif op == 'IN':
                placeholders = ', '.join(f"${len(params) + i}" for i in range(1, len(value) + 1))
                params.extend(value)
                conditions.append(f"{field} IN ({placeholders})")
            elif op == 'LIKE':
                conditions.append(f"{field} LIKE ${len(params) + 1}")
                params.append(value)
            else:
                placeholder = f"${len(params) + 1}"
                params.append(value)
                conditions.append(f"{field} {op} {placeholder}")
        elif isinstance(cond, dict) and 'AND' in cond:
            inner = [f"({c})" for c in cond['AND']]
            conditions.append(f"({' AND '.join(inner)})")
        elif isinstance(cond, dict) and 'OR' in cond:
            inner = [f"({c})" for c in cond['OR']]
            conditions.append(f"({' OR '.join(inner)})")
        else:
            raise ValueError(f"Unsupported condition format: {cond}")

    def process_where(where_dict):
        for k, v in where_dict.items():
            if isinstance(v, dict) and len(v) == 3:
                add_condition({k: v['op'], 'value': v['value']})
            else:
                raise ValueError(f"Unsupported condition format: {v}")

    process_where(where)
    for j in joins:
        join_type = j.get('type', 'INNER').upper()
        join_table = j['table']
        on_conditions = j['on']
        on_parts = []
        for left, right in on_conditions.items():
            left_col, right_col = left.split('.') if '.' in left else (left, right)
            right_col = right.split('.') if '.' in right else right
            on_parts.append(f"{left_col} {join_type} {right_col}")
        conditions.append(f"JOIN {join_table} ON {' AND '.join(on_parts)}")

    # HAVING clause
    having_clause = ""
    if having:
        having_clause = f"HAVING {' AND '.join([f'{c[0]} {c[1]} {c[2]}' for c in [process_where(h) for h in having.get('where', {}).items()])}}"

    # Subqueries in IN
    def process_subquery(subquery_dict, prefix=''):
        nonlocal subquery_params
        q_table = subquery_dict['table']
        q_select = subquery_dict.get('select', [])
        q_where = subquery_dict.get('where', {})
        q_group = subquery_dict.get('groupBy', [])
        q_having = subquery_dict.get('having', None)
        q_order = subquery_dict.get('orderBy', [])
        q_limit = subquery_dict.get('limit')
        q_offset = subquery_dict.get('offset')

        # Build SELECT for subquery
        sub_select = ', '.join(q_select)
        if sub_group:
            sub_group = f"GROUP BY {', '.join(f'{col} AS {col}' for col in sub_group)}"
        else:
            sub_group = ''
        sub_having = f"HAVING {' AND '.join([f'{c[0]} {c[1]} {c[2]}' for c in [process_where(h) for h in q_having.get('where', {}).items()])}}" if q_having else ''
        sub_order = f"ORDER BY {', '.join(f'{col} {dir or 'ASC'}' for col, dir in q_order)}" if q_order else ''
        sub_limit = f"LIMIT {q_limit}" if q_limit else ''
        sub_offset = f"OFFSET {q_offset}" if q_offset else ''

        sub_where = []
        if q_where:
            for wh in q_where.items():
                if isinstance(wh, dict) and len(wh) == 3:
                    add_condition({wh[0]: wh[1], 'value': wh[2]})
                else:
                    raise ValueError(f"Unsupported subquery condition: {wh}")
        # Build JOINs for subquery
        sub_joins = []
        for j in subquery_dict.get('joins', []):
            join_type = j.get('type', 'INNER').upper()
            j_table = j['table']
            on_conditions = j['on']
            on_parts = []
            for l, r in on_conditions.items():
                l_col, r_col = l.split('.') if '.' in l else (l, r)
                r_col = r.split('.') if '.' in r else r
                on_parts.append(f"{l_col} {join_type} {r_col}")
            sub_joins.append(f"JOIN {j_table} ON {' AND '.join(on_parts)}")

        # Build subquery SQL
        sub_sql = f"SELECT {sub_select}"
        if sub_joins:
            sub_sql += ' ' + ' '.join(sub_joins)
        sub_sql += f" FROM {q_table}"
        if sub_group:
            sub_sql += f" {sub_group}"
        if q_having:
            sub_sql += f" {sub_having}"
        if sub_order:
            sub_sql += f" {sub_order}"
        if sub_limit:
            sub_sql += f" {sub_limit}"
        if sub_offset:
            sub_sql += f" {sub_offset}"
        sub_sql = sub_sql.strip()
        # Add subquery alias
        alias = prefix + (f" AS {sub_table}" if prefix else sub_table)
        sub_sql = sub_sql.replace(f"FROM {q_table}", alias)
        subquery_params.append(sub_sql)
        return sub_sql

    # Process IN with subquery
    for i, s in enumerate(select):
        if isinstance(s, dict) and 'expr' in s:
            expr = s['expr']
            as_name = s.get('as', '')
            params_inner = []
            if 'IN' in s:
                subquery_sql = process_subquery({
                    'table': table,
                    'select': [expr],
                    'where': having if having else {},
                    'subqueries': subqueries,
                    'groupBy': groupBy,
                    'orderBy': orderBy,
                    'limit': limit,
                    'offset': offset
                })
                placeholder = f"${len(params) + i + 1}"
                conditions.append(f"{expr} IN ({placeholder})")
                params.extend([subquery_sql, placeholder])
                subquery_params.append(subquery_sql)
            else:
                conditions.append(expr)
        elif isinstance(s, str):
            conditions.append(s)

    select_clause = ', '.join(select)
    order_by_clause = ', '.join([f"{b['field']} {b.get('dir', 'ASC')}" for b in orderBy]) if orderBy else ''
    group_by_clause = ', '.join(groupBy) if groupBy else ''
    having_clause = f"HAVING {' AND '.join([f'{c[0]} {c[1]} {c[2]}' for c in [process_where(h) for h in having.get('where', {}).items()])}}" if having else ''

    limit_clause = f"LIMIT {limit}" if limit is not None else ""
    offset_clause = f"OFFSET {offset}" if offset is not None else ""

    sql_parts = [
        f"SELECT {select_clause}",
        *conditions,
        f"GROUP BY {group_by_clause}" if groupBy else '',
        having_clause,
        f"ORDER BY {order_by_clause}" if orderBy else '',
        limit_clause,
        offset_clause
    ]
    sql = ' '.join([p for p in sql_parts if p])
    params = params + subquery_params
    return {"sql": sql, "params": params}
