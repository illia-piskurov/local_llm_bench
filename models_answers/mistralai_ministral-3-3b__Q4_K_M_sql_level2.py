def compile_query(query: dict) -> dict:
    def _build_where_clause(cond):
        if isinstance(cond, dict) and 'AND' in cond:
            return f"({', '.join(_build_where_clause(c) for c in cond['AND'])}) AND"
        elif isinstance(cond, dict) and 'OR' in cond:
            return f"({', '.join(_build_where_clause(c) for c in cond['OR'])}) OR"
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
            elif op == 'IN':
                params = []
                def _collect_in_params(v):
                    if isinstance(v, list):
                        for item in v:
                            params.append(item)
                    else:
                        params.append(v)
                _collect_in_params(value)
                placeholders = ', '.join(['?'] * len(params))
                return f"{field} IN ({placeholders})"
            elif op == 'IS NULL':
                return f"{field} IS NULL"
            elif op == 'IS NOT NULL':
                return f"{field} IS NOT NULL"
            elif op == 'LIKE':
                return f"{field} LIKE ?"
            else:
                raise ValueError(f"Unsupported operator: {op}")

    def _build_join_clause(joins):
        if not joins:
            return ""
        clauses = []
        for join in joins:
            join_type = join.get('type', 'INNER')
            table = join['table']
            on_cond = join['on']
            left_col, right_col = next(iter(on_cond.items()))
            clauses.append(f"{join_type} JOIN {table} ON {left_col} = {right_col}")
        return ", ".join(clauses)

    def _build_group_by_clause(group_columns):
        if not group_columns:
            return ""
        return "GROUP BY " + ", ".join(group_columns)

    # Build SQL parts
    select_clause = "SELECT " + (", ".join(query['select']) if query['select'] else "*")
    where_clause = ""
    join_clause = ""
    group_by_clause = ""

    if 'where' in query:
        where_clause = _build_where_clause(query['where'])

    if 'joins' in query:
        join_clause = _build_join_clause(query['joins'])

    if 'groupBy' in query:
        group_by_clause = _build_group_by_clause(query['groupBy'])

    order_by_clause = ""
    if 'orderBy' in query:
        def _build_order_by_clause(order_conditions):
            clauses = []
            for cond in order_conditions:
                field, dir_ = cond.get('field'), cond.get('dir', 'ASC')
                clauses.append(f"{field} {'DESC' if dir_ == 'DESC' else 'ASC'}")
            return ", ".join(clauses)
        order_by_clause = f"ORDER BY {_build_order_by_clause(query['orderBy'])}"

    limit_clause = ""
    offset_clause = ""
    if 'limit' in query:
        limit_clause = f"LIMIT {query['limit']}"
    if 'offset' in query:
        offset_clause = f"OFFSET {query['offset']}"

    sql = f"SELECT {select_clause} FROM {query['table']}"
    if join_clause:
        sql += " " + join_clause
    if where_clause:
        sql += " WHERE " + where_clause
    if group_by_clause:
        sql += " " + group_by_clause
    if order_by_clause:
        sql += " " + order_by_clause
    if limit_clause:
        sql += " " + limit_clause
    if offset_clause:
        sql += " " + offset_clause

    # Collect parameters in left-to-right traversal order
    params = []
    param_idx = 1

    def _collect_params(cond):
        nonlocal params, param_idx
        if isinstance(cond, dict) and 'AND' in cond:
            for c in cond['AND']:
                _collect_params(c)
        elif isinstance(cond, dict) and 'OR' in cond:
            for c in cond['OR']:
                _collect_params(c)
        else:
            _, op, value = cond
            if op == '=' or op == '!=' or op == '>' or op == '<' or op == '>=' or op == '<=':
                params.append(value)
            elif op == 'IN':
                def _collect_in_params(v):
                    nonlocal param_idx
                    if isinstance(v, list):
                        for item in v:
                            params.append(item)
                    else:
                        params.append(v)
                _collect_in_params(value)
            elif op == 'LIKE':
                params.append(value)

    _collect_params(query.get('where', {}))
    return {"sql": sql.replace("?", f"${param_idx}", 1), "params": params}
