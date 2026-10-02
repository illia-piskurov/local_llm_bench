def compile_query(query: dict) -> dict:
    params = []

    def build_where(node: dict) -> str:
        if "AND" in node:
            conditions = [build_where(c) for c in node["AND"]]
            if len(conditions) > 1:
                return f"({ ' AND '.join(conditions) })"
            return conditions[0]
        
        if "OR" in node:
            conditions = [build_where(c) for c in node["OR"]]
            if len(conditions) > 1:
                return f"({ ' OR '.join(conditions) })"
            return conditions[0]
        
        # Leaf node: { field: str, op: str, value: any }
        params.append(node["value"])
        return f"{node['field']} {node['op']} ${len(params)}"

    # 1. SELECT clause
    select_cols = query.get("select", ["*"])
    select_str = ", ".join(select_cols)
    
    # 2. FROM clause
    table_name = query["table"]
    
    sql_parts = [f"SELECT {select_str} FROM {table_name}"]

    # 3. WHERE clause
    where_node = query.get("where")
    if where_node:
        where_clause = build_where(where_node)
        sql_parts.append(f"WHERE {where_clause}")

    # 4. ORDER BY clause
    order_by_list = query.get("orderBy")
    if order_by_list:
        order_parts = []
        for item in order_by_list:
            direction = item.get("dir", "ASC")
            order_parts.append(f"{item['field']} {direction}")
        sql_parts.append(f"ORDER BY {', '.join(order_parts)}")

    # 5. LIMIT clause
    if "limit" in query:
        sql_parts.append(f"LIMIT {query['limit']}")

    # 6. OFFSET clause
    if "offset" in query:
        sql_parts.append(f"OFFSET {query['offset']}")

    return {
        "sql": " ".join(sql_parts),
        "params": params
    }
