def compile_query(query: dict) -> dict:
    if not query:
        return {"sql": "", "params": []}
    
    table = query["table"]
    select = query.get("select", ["*"])
    where = query.get("where")
    order_by = query.get("orderBy", [])
    limit = query.get("limit")
    offset = query.get("offset")
    joins = query.get("joins")
    groupBy = query.get("groupBy")
    
    # Build SELECT part
    select_sql = ", ".join(select)
    select_sql += " FROM " + table
    
    # Process JOINs
    from_clause = []
    if joins:
        for join in joins:
            type_ = join.get("type", "INNER")
            table_name = join["table"]
            on = join["on"]
            from_clause.append(f"JOIN {table_name} ON {on}")
    
    # Build FROM clause
    from_sql = " ".join(from_clause) if from_clause else ""
    
    # Process WHERE clause
    where_clause = ""
    params = []
    
    if where:
        # Parse the where AST into conditions
        if isinstance(where, dict) and where.get("AND"):
            conditions = where["AND"]
            parts = []
            for i, cond in enumerate(conditions):
                part = build_condition_part(cond, params)
                if i > 0:
                    parts.append(" AND ")
                parts.append(part)
            where_clause = f"({parts.join('')})"
        elif isinstance(where, dict) and where.get("OR"):
            conditions = where["OR"]
            parts = []
            for i, cond in enumerate(conditions):
                part = build_condition_part(cond, params)
                if i > 0:
                    parts.append(" OR ")
                parts.append(part)
            where_clause = f"({parts.join('')})"
        else:
            # Single condition
            part = build_condition_part(where, params)
            where_clause = part
    
    # Build ORDER BY
    order_sql = ""
    if order_by:
        order_sql = "ORDER BY "
        for cond in order_by:
            field = cond["field"]
            dir = cond.get("dir", "ASC")
            order_sql += f"{field} {dir}, "
        order_sql = order_sql.rstrip(", ")
    
    # Add LIMIT and OFFSET
    if limit is not None:
        limit_str = f"LIMIT {limit}"
    else:
        limit_str = ""
    if offset is not None:
        offset_str = f"OFFSET {offset}"
    else:
        offset_str = ""
    
    full_sql = (
        f"{select_sql} {from_sql} {where_clause} {order_sql} {limit_str} {offset_str}"
    )
    
    # Handle GROUP BY
    if groupBy:
        full_sql += " GROUP BY " + ", ".join(groupBy)
    
    return {"sql": full_sql, "params": params}

def build_condition_part(condition: dict, params) -> str:
    if not condition:
        return ""
    
    field = condition["field"]
    op = condition["op"]
    value = condition["value"]
    
    # Handle IS NULL/IS NOT NULL
    if op in ["IS NULL", "IS NOT NULL"]:
        cond_str = f"{field} {op}"
        return cond_str
    
    # Handle IN
    if op == "IN":
        if isinstance(value, list):
            placeholders = [f"${len(params)+1}" for _ in value]
            params.extend(value)
            return f"{field} IN ({', '.join(placeholders)})"
        else:
            param_placeholder = f"${len(params)+1}"
            params.append(value)
            return f"{field} IN ({param_placeholder})"
    
    # Handle LIKE
    if op == "LIKE":
        if isinstance(value, str):
            return f"{field} LIKE {value}"
        else:
            param_placeholder = f"${len(params)+1}"
            params.append(value)
            return f"{field} LIKE {param_placeholder}"
    
    # Default case: simple comparison
    param_placeholder = f"${len(params)+1}"
    params.append(value)
    return f"{field} {op} {param_placeholder}"
