def compile_query(query):
    table = query["table"]
    select_clause = ", ".join(query.get("select", ["*"]))
    where_node = query.get("where")
    order_by = query.get("orderBy", [])
    limit = query.get("limit")
    offset = query.get("offset")

    sql_parts = [f"SELECT {select_clause} FROM {table}"]
    params = []
    placeholder_counter = [1]

    def compile_where(node):
        if isinstance(node, dict):
            if "field" in node and "op" in node and "value" in node:
                placeholder = f"${placeholder_counter[0]}"
                params.append(node["value"])
                placeholder_counter[0] += 1
                return f"{node['field']} {node['op']} {placeholder}"
            for op_key in ("AND", "OR"):
                if op_key in node:
                    conditions = node[op_key]
                    fragments = []
                    for cond in conditions:
                        fragments.append(compile_where(cond))
                    if len(fragments) > 1:
                        joined = f" ({' '.join(fragments)} {op_key.lower()} )"
                    else:
                        joined = fragments[0]
                    return joined
        return ""

    if where_node:
        where_sql = compile_where(where_node)
        if where_sql:
            sql_parts.append(f"WHERE {where_sql}")

    if order_by:
        order_parts = []
        for ob in order_by:
            direction = ob.get("dir", "ASC").upper()
            order_parts.append(f"{ob['field']} {direction}")
        sql_parts.append("ORDER BY " + ", ".join(order_parts))

    if offset is not None:
        sql_parts.append(f"OFFSET {offset}")
    if limit is not None:
        sql_parts.append(f"LIMIT {limit}")

    sql = " ".join(sql_parts)
    return {"sql": sql, "params": params}
