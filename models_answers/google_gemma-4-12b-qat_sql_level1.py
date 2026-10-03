def compile_query(query: dict) -> dict:
    params = []

    def build_where(condition: dict) -> str:
        if "AND" in condition:
            sub_conditions = condition["AND"]
            if len(sub_conditions) > 1:
                parts = [f"({build_where(c)})" for c in sub_conditions]
                return " AND ".join(parts)
            else:
                return build_where(sub_conditions[0])
        
        if "OR" in condition:
            sub_conditions = condition["OR"]
            if len(sub_conditions) > 1:
                parts = [f"({build_where(c)})" for c in sub_conditions]
                return " OR ".join(parts)
            else:
                return build_where(sub_conditions[0])
        
        # Leaf condition: { field: str, op: str, value: any }
        field = condition.get("field")
        op = condition.get("op")
        value = condition.get("value")
        params.append(value)
        return f"{field} {op} ${len(params)}"

    # 1. SELECT
    select_clause = ", ".join(query.get("select", ["*"]))
    
    # 2. FROM
    table = query.get("table")
    
    # 3. WHERE
    where_clause = ""
    if "where" in query and query["where"]:
        where_clause = " WHERE " + build_where(query["where"])
    
    # 4. ORDER BY
    order_clause = ""
    if "orderBy" in query and query["orderBy"]:
        orders = []
        for item in query["orderBy"]:
            field = item.get("field")
            direction = item.get("dir", "ASC")
            orders.append(f"{field} {direction}")
        order_clause = " ORDER BY " + ", ".join(orders)
    
    # 5. LIMIT & OFFSET
    limit_clause = ""
    if "limit" in query:
        limit_clause = f" LIMIT {query['limit']}"
        
    offset_clause = ""
    if "offset" in query:
        offset_clause = f" OFFSET {query['offset']}"

    sql = f"SELECT {select_clause} FROM {table}{where_clause}{order_clause}{limit_clause}{offset_clause}"
    
    return {
        "sql": sql,
        "params": params
    }
