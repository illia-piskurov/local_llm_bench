def compile_query(query: dict) -> dict:
    def _build_where_clause(cond):
        if isinstance(cond, dict) and 'AND' in cond:
            return f"({', '.join(_build_where_clause(c) for c in cond['AND'])})"
        elif isinstance(cond, dict) and 'OR' in cond:
            return f"({', '.join(_build_where_clause(c) for c in cond['OR'])})"
        else:
            field, op, value = cond
            if op == '=':
                return f"{field} = ?"
            elif op == '!=':
                return f"{field} != ?"
            elif op == '>':
                return f"{field} > ?"
            elif op == '<':
                return f"{field} < ?"
            elif op == '>=':
                return f"{field} >= ?"
            elif op == '<=':
                return f"{field} <= ?"
            else:
                raise ValueError(f"Unsupported operator: {op}")

    def _build_order_by_clause(order_conditions):
        if not order_conditions:
            return ""
        clauses = []
        for cond in order_conditions:
            field, dir_ = cond.get('field'), cond.get('dir', 'ASC')
            clauses.append(f"{field} {'DESC' if dir_ == 'DESC' else 'ASC'}")
        return " ORDER BY " + ", ".join(clauses)

    def _build_limit_offset():
        limit = query.get('limit', None)
        offset = query.get('offset', None)
        parts = []
        if limit is not None:
            parts.append(f"LIMIT {limit}")
        if offset is not None:
            parts.append(f"OFFSET {offset}")
        return " ".join(parts)

    # Build SELECT clause
    select_clause = "SELECT "
    if query.get('select') == ['*']:
        select_clause += "*"
    else:
        select_clause += ", ".join(query['select'])

    # Build WHERE clause with parameter placeholders
    where_placeholders = []
    params = []
    if 'where' in query and query['where'] is not None:
        def _traverse_and_collect(cond):
            nonlocal params
            if isinstance(cond, dict) and 'AND' in cond:
                for c in cond['AND']:
                    _traverse_and_collect(c)
            elif isinstance(cond, dict) and 'OR' in cond:
                for c in cond['OR']:
                    _traverse_and_collect(c)
            else:
                _, op, value = cond
                where_placeholders.append(f"?")
                params.append(value)

        _traverse_and_collect(query['where'])
        where_clause = _build_where_clause(query['where'])
    else:
        where_clause = ""

    # Build SQL query
    sql = f"{select_clause} FROM {query['table']}"
    if where_clause:
        sql += " WHERE " + where_clause
    sql += _build_order_by_clause(query.get('orderBy', []))
    sql += _build_limit_offset()

    return {"sql": sql, "params": params}
