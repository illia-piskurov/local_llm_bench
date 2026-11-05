def compile_query(query):
    table = query['table']
    select = query.get('select', ['*'])
    where_cond = query.get('where')
    joins = query.get('joins', [])
    group_by = query.get('groupBy', [])
    order_by = query.get('orderBy', [])
    limit = query.get('limit')
    offset = query.get('offset')

    params = []
    sql_parts = []

    # SELECT
    cols = [f" {col}" for col in select]
    sql_parts.append(f"SELECT {', '.join(cols)}")

    # JOINs
    if joins:
        join_parts = []
        for join in joins:
            join_type = join.get('type', 'INNER')
            join_table = join['table']
            on_clause = join['on']
            join_str = f"{join_type} JOIN {join_table} ON " + " AND ".join(f"{left_col} = {right_col}" for left_col, right_col in on_clause)
            join_parts.append(join_str)
        sql_parts.append(" ".join(join_parts))

    # WHERE with extended operators
    where_expr = "TRUE"
    if where_cond:
        flat_conds = []
        for cond in where_cond:
            if isinstance(cond, dict):
                if cond.get('AND'):
                    flat_conds.append(f"({', '.join(cond['AND'])})")
                elif cond.get('OR'):
                    flat_conds.append(f"({', '.join(cond['OR'])})")
                else:
                    field = cond['field']
                    op = cond['op']
                    val = cond['value']
                    if op == 'IN':
                        vals = [f"${{1}}" for _ in val]
                        sql_parts.append(f"    {field} IN ({', '.join(vals)})")
                        params.extend(val)
                    elif op == 'IS NULL' or op == 'IS NOT NULL':
                        sql_parts.append(f"    {field} {op} NULL")
                    elif op == 'LIKE':
                        sql_parts.append(f"    {field} LIKE $1")
                        params.append(val)
                    else:
                        # simple equality placeholder
                        placeholder = f"${{1}}" if len(flat_conds) == 1 else f"${{2}}"
                        sql_parts.append(f"    {field} {op} {placeholder}")
                        params.append(val)
            else:
                # should not happen
                pass
        where_expr = " AND ".join(flat_conds)
    else:
        where_expr = "TRUE"

    sql_parts.append(f"WHERE {where_expr}")

    # GROUP BY
    if group_by:
        sql_parts.append(f"GROUP BY {', '.join(group_by)}")

    # ORDER BY
    if order_by:
        dirs = [d.get('dir', 'ASC') for d in order_by]
        sql_parts.append(f"ORDER BY " + ", ".join(f"{d['field']} {d['dir']}" for d in order_by))
    else:
        sql_parts.append("ORDER BY ASC")

    # LIMIT / OFFSET
    if limit:
        sql_parts.append(f"LIMIT {limit}")
    if offset:
        sql_parts.append(f"OFFSET {offset}")

    sql = " ".join(sql_parts)
    return {"sql": sql, "params": params}
