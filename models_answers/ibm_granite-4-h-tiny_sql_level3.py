def compile_query(query: dict) -> dict:
    def build_where(node):
        if isinstance(node, dict):
            parts = []
            for key, value in node.items():
                if key == 'AND':
                    sub_parts = [build_where(c) for c in value]
                    parts.append(f"({') AND ('.join(sub_parts)})")
                elif key == 'OR':
                    sub_parts = [build_where(c) for c in value]
                    parts.append(f"({') OR ('.join(sub_parts)})")
                else:
                    field, op, val = value
                    if isinstance(val, (int, float)):
                        params.append(val)
                        parts.append(f"{field} {op}")
                    elif isinstance(val, str):
                        if op == 'IN':
                            placeholders = ', '.join(['%s'] * len(val))
                            params.extend(val)
                            parts.append(f"{field} IN ({placeholders})")
                        elif op in ['IS NULL', 'IS NOT NULL']:
                            parts.append(f"{field} {op}")
                        elif op == 'LIKE':
                            params.append(val)
                            parts.append(f"{field} LIKE %s")
                    else:
                        raise ValueError("Unsupported value type for operator")
            return ' AND '.join(parts) if len(parts) > 1 else parts[0] if parts else ''
        return ''

    def build_select(node):
        if node.get('select') is None:
            return '*'
        cols = node['select']
        if isinstance(cols, str):
            cols = [cols]
        return ', '.join(cols)

    def build_having(node):
        if node.get('having') is None:
            return ''
        parts = []
        for key, value in node['having'].items():
            if key == 'AND':
                sub_parts = [build_where(c) for c in value]
                parts.append(f"({') AND ('.join(sub_parts)})")
            elif key == 'OR':
                sub_parts = [build_where(c) for c in value]
                parts.append(f"({') OR ('.join(sub_parts)})")
            else:
                field, op, val = value
                if isinstance(val, (int, float)):
                    params.append(val)
                    parts.append(f"{field} {op}")
                elif isinstance(val, str):
                    if op == 'IN':
                        placeholders = ', '.join(['%s'] * len(val))
                        params.extend(val)
                        parts.append(f"{field} IN ({placeholders})")
                    elif op in ['IS NULL', 'IS NOT NULL']:
                        parts.append(f"{field} {op}")
                    elif op == 'LIKE':
                        params.append(val)
                        parts.append(f"{field} LIKE %s")
                else:
                    raise ValueError("Unsupported value type for operator")
        return ' AND '.join(parts) if len(parts) > 1 else parts[0] if parts else ''

    def build_order_by(node):
        if 'orderBy' not in node or not node['orderBy']:
            return ''
        parts = []
        for item in node['orderBy']:
            field = item.get('field')
            direction = item.get('dir', 'ASC')
            parts.append(f"{field} {direction}")
        return ' ORDER BY ' + ', '.join(parts)

    def build_limit_offset(node):
        limit = node.get('limit')
        offset = node.get('offset')
        parts = []
        if limit is not None:
            parts.append(f"LIMIT {limit}")
        if offset is not None:
            parts.append(f"OFFSET {offset}")
        return ' '.join(parts)

    def build_joins(node):
        if 'joins' not in node or not node['joins']:
            return ''
        parts = []
        for join in node['joins']:
            type_ = join.get('type', 'INNER')
            table = join.get('table')
            on_clause = join.get('on')
            parts.append(f"{type_} JOIN {table}")
            if on_clause:
                parts.append(" ON ")
                parts.extend(build_where(on_clause))
        return ' '.join(parts)

    def build_expression(expr_node):
        expr = expr_node['expr']
        alias = expr_node.get('as', '')
        params_copy = params.copy()
        subquery_params, subquery_sql = compile_query({'select': {'expr': expr}, 'params': []})['params'], \
                                     compile_query({'select': {'expr': expr}, 'params': []})['sql']
        for param in subquery_params:
            params.append(param)
        return f"{alias} AS {subquery_sql}" if alias else subquery_sql

    def build_select_with_expressions(node):
        selected = node.get('select')
        if isinstance(selected, str):
            selected = [selected]
        result = []
        for item in selected:
            if isinstance(item, dict) and 'expr' in item and 'as' in item:
                expr_sql = build_expression(item)
                result.append(expr_sql)
            else:
                result.append(str(item))
        return ', '.join(result)

    params = []

    table = query.get('table')
    select_clause = build_select_with_expressions(query)
    having_clause = build_having(query)
    where_clause = build_where(query.get('where', {}))
    group_by_clause = query.get('groupBy')
    order_by_clause = build_order_by(query)
    limit_offset_clause = build_limit_offset(query)
    joins_clause = build_joins(query)

    sql = f"SELECT {select_clause}"
    if joins_clause:
        sql += f" {joins_clause}"
    sql += f" FROM {table}"
    if where_clause:
        sql += f" WHERE {where_clause}"
    if having_clause:
        sql += f" HAVING {having_clause}"
    if group_by_clause:
        sql += f" GROUP BY {', '.join(group_by_clause)}"
    if order_by_clause:
        sql += f" {order_by_clause}"
    if limit_offset_clause:
        sql += f" {limit_offset_clause}"

    return {"sql": sql, "params": params}
