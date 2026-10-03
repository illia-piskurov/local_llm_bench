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
                        params.append(val)
                        parts.append(f"{field} = %s")
            return ' AND '.join(parts) if len(parts) > 1 else parts[0] if parts else ''
        return ''

    def build_select(node):
        if node.get('select') is None:
            return '*'
        cols = node['select']
        if isinstance(cols, str):
            cols = [cols]
        return ', '.join(cols)

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

    params = []

    table = query.get('table')
    select_clause = build_select(query)
    where_clause = build_where(query.get('where', {}))
    order_by_clause = build_order_by(query)
    limit_offset_clause = build_limit_offset(query)

    sql = f"SELECT {select_clause} FROM {table}"
    if where_clause:
        sql += f" WHERE {where_clause}"
    if order_by_clause:
        sql += f" {order_by_clause}"
    if limit_offset_clause:
        sql += f" {limit_offset_clause}"

    return {"sql": sql, "params": params}
