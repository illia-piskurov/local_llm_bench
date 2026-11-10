def compile_query(query: dict) -> dict:
    sql = []
    params = []

    sql.append("SELECT")
    columns = query.get("select", ["*"])
    sql.append(", ".join(columns))

    joins = query.get("joins", [])
    if joins:
        sql.append("FROM")
        sql.append(query["table"])
        for join in joins:
            join_type = join.get("type", "INNER")
            sql.append(f"{join_type} JOIN {join['table']}")
            on = join.get("on", {})
            left_col = next(iter(on))
            right_col = on[left_col]
            sql.append(f"ON {left_col} = {right_col}")

    where = query.get("where")
    if where:
        sql.append("WHERE")
        cond_sql, params = _compile_condition(where, params)
        sql.append(cond_sql)

    if query.get("groupBy"):
        sql.append("GROUP BY")
        sql.append(", ".join(query["groupBy"]))

    if query.get("orderBy"):
        sql.append("ORDER BY")
        for item in query["orderBy"]:
            field = item["field"]
            direction = item.get("dir", "ASC")
            sql.append(f"{field} {direction}")

    if query.get("limit") is not None:
        sql.append(f"LIMIT {query['limit']}")

    if query.get("offset") is not None:
        sql.append(f"OFFSET {query['offset']}")

    return {"sql": " ".join(sql), "params": params}


def _compile_condition(cond, params):
    if isinstance(cond, list):
        parts = [_compile_condition(c, params) for c in cond]
        return " AND ".join(parts), params

    if isinstance(cond, dict):
        if "AND" in cond:
            conds = cond["AND"]
            if len(conds) > 1:
                parts = [_compile_condition(c, params) for c in conds]
                return f"({ ' AND '.join(p[0] for p in parts) })", params
            return parts[0][0], params

        if "OR" in cond:
            conds = cond["OR"]
            if len(conds) > 1:
                parts = [_compile_condition(c, params) for c in conds]
                return f"({ ' OR '.join(p[0] for p in parts) })", params
            return parts[0][0], params

        return _compile_leaf(cond, params)

    return _compile_leaf(cond, params)


def _compile_leaf(cond, params):
    field = cond["field"]
    op = cond["op"]
    value = cond["value"]

    if op == "IS NULL":
        return f"{field} IS NULL"

    if op == "IS NOT NULL":
        return f"{field} IS NOT NULL"

    if op == "IN":
        placeholders = ", ".join(f"${i + 1}" for i in range(len(value)))
        params.extend(value)
        return f"{field} IN ({placeholders})"

    if op == "LIKE":
        placeholder = f"${len(params) + 1}"
        params.append(value)
        return f"{field} LIKE {placeholder}"

    placeholder = f"${len(params) + 1}"
    params.append(value)
    return f"{field} {op} {placeholder}"
