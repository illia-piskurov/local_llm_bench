def compile_query(query):
    table = query['table']
    select = query.get('select', ['*'])
    where = query.get('where')
    order_by = query.get('orderBy', [])
    limit = query.get('limit')
    offset = query.get('offset')

    placeholders = []
    params = []

    def _compile_cond(cond):
        if isinstance(cond, dict) and 'field' in cond:
            p = f"${(len(placeholders)+1)}"
            placeholders.append(p)
            params.append(None)
            return f"{cond['field']} {cond['op']} $placeholder"
        elif isinstance(cond, list):
            op = cond[0]
            sub_conds = [c for c in cond if c is not None]
            parts = [_compile_cond(c) for c in sub_conds]
            return f"({' '.join(parts)} {op})"
        else:
            raise ValueError(f"Unsupported condition: {cond}")

    where_str = ""
    if where:
        flat = []
        def _flatten(lst):
            for x in lst:
                if isinstance(x, dict) and 'field' in x:
                    flat.append(x)
                elif isinstance(x, list):
                    _flatten(x)
        if isinstance(where, dict):
            flat = [_compile_cond(where)]
        else:  # where is a list of condition dicts
            flat = [c for c in where if isinstance(c, dict) and 'field' in c]
        where_str = " AND ".join(_compile_cond(c) for c in flat)

    sql = f"SELECT {' '.join(select)} FROM {table}"
    if where_str:
        sql += f" WHERE ({where_str})"
    order_part = ""
    if order_by:
        order_clauses = []
        for o in order_by:
            field = o['field']
            dir = o.get('dir', 'ASC')
            order_clauses.append(f"{field} {dir}")
        order_part = " ORDER BY " + " AND ".join(order_clauses)
    sql += order_part
    if limit:
        sql += f" LIMIT {limit}"
    if offset:
        sql += f" OFFSET {offset}"

    return {"sql": sql, "params": params}
