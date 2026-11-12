def compile_query(query: dict) -> dict:
    def compile_condition(condition):
        if isinstance(condition, dict):
            op = condition['op']
            if op in ('=', '!=', '>', '<', '>=', '<=', 'IN'):
                if op == 'IN':
                    values = condition['value']
                    placeholders = ', '.join(f"${i+1}" for i in range(len(values)))
                    return f"{condition['field']} {op} ({placeholders})"
                else:
                    return f"{condition['field']} {op} ${len(params)+1}"
            elif op == 'LIKE':
                return f"{condition['field']} LIKE ${len(params)+1}"
            elif op in ('IS NULL', 'IS NOT NULL'):
                return f"{condition['field']} {op}"
            elif op in ('AND', 'OR'):
                return ' {} '.format(' '.join(compile_condition(c) for c in condition[op]))
            else:
                raise ValueError(f"Unsupported operator: {op}")
        return str(condition)

    def compile_order_by(order_by):
        return ', '.join(f"{item['field']} {item.get('dir', 'ASC')}" for item in order_by)

    def compile_joins(joins):
        join_clauses = []
        for join in joins:
            join_type = join.get('type', 'INNER').upper()
            table = join['table']
            on = join['on']
            on_clauses = ' '.join(f"{left} = {right}" for left, right in on.items())
            join_clauses.append(f"{join_type} JOIN {table} ON {on_clauses}")
        return ' '.join(join_clauses)

    table = query['table']
    select = query.get('select', ['*'])
    where = query.get('where', {})
    order_by = query.get('orderBy', [])
    limit = query.get('limit', None)
    offset = query.get('offset', None)
    joins = query.get('joins', [])
    group_by = query.get('groupBy', [])
    params = []

    sql = f"SELECT {', '.join(select)} FROM {table}"
    if joins:
        sql += f" {compile_joins(joins)}"
    if where:
        sql += f" WHERE {compile_condition(where)}"
    if group_by:
        sql += f" GROUP BY {', '.join(group_by)}"
    if order_by:
        sql += f" ORDER BY {compile_order_by(order_by)}"
    if limit is not None:
        sql += f" LIMIT {limit}"
    if offset is not None:
        sql += f" OFFSET {offset}"

    return {"sql": sql, "params": params}

# Example usage:
# query = {
#     "table": "users",
#     "select": ["name", "age"],
#     "where": {
#         "AND": [
#             {"field": "age", "op": ">", "value": 18},
#             {"field": "name", "op": "LIKE", "value": "A%"}
#         ]
#     },
#     "joins": [
#         {"type": "LEFT", "table": "orders", "on": {"users.id": "orders.user_id"}}
#     ],
#     "groupBy": ["orders.status"],
#     "orderBy": [{"field": "name", "dir": "ASC"}],
#     "limit": 10
# }
# print(compile_query(query))
