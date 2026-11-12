def compile_query(query: dict) -> dict:
    def compile_condition(condition, param_index):
        if isinstance(condition, dict):
            op = condition['op']
            if op in ('=', '!=', '>', '<', '>=', '<=', 'IN'):
                if op == 'IN':
                    values = condition['value']
                    placeholders = ', '.join(f"${param_index + i}" for i in range(len(values)))
                    param_index += len(values)
                    return f"{condition['field']} {op} ({placeholders})", param_index
                else:
                    return f"{condition['field']} {op} ${param_index}", param_index
            elif op == 'LIKE':
                return f"{condition['field']} LIKE ${param_index}", param_index
            elif op in ('IS NULL', 'IS NOT NULL'):
                return f"{condition['field']} {op}", param_index
            elif op in ('AND', 'OR'):
                left, param_index = compile_condition(condition[0], param_index)
                right, param_index = compile_condition(condition[1], param_index)
                return f"({left} {condition['op']} {right})", param_index
            else:
                raise ValueError(f"Unsupported operator: {op}")
        return str(condition), param_index

    def compile_select(select, param_index):
        compiled_select = []
        for item in select:
            if isinstance(item, dict):
                expr, param_index = compile_condition(item['expr'], param_index)
                compiled_select.append(f"{item['as']}: {expr}")
            else:
                compiled_select.append(item)
        return ', '.join(compiled_select), param_index

    def compile_order_by(order_by):
        return ', '.join(f"{item['field']} {item.get('dir', 'ASC')}" for item in order_by)

    def compile_joins(joins):
        join_clauses = []
        for join in joins:
            join_type = join.get('type', 'INNER').upper()
            table = join['table']
            on = join['on']
            on_clauses, param_index = compile_condition(on, param_index)
            join_clauses.append(f"{join_type} JOIN {table} ON {on_clauses}")
        return ' '.join(join_clauses)

    table = query['table']
    select = query.get('select', [])
    where = query.get('where', {})
    having = query.get('having', {})
    order_by = query.get('orderBy', [])
    limit = query.get('limit', None)
    offset = query.get('offset', None)
    joins = query.get('joins', [])
    group_by = query.get('groupBy', [])

    sql = f"SELECT {compile_select(select, 1)} FROM {table}"
    if joins:
        sql += f" {compile_joins(joins)}"
    if where:
        sql += f" WHERE {compile_condition(where, 2)}"
    if having:
        sql += f" HAVING {compile_condition(having, 3)}"
    if group_by:
        sql += f" GROUP BY {', '.join(group_by)}"
    if order_by:
        sql += f" ORDER BY {compile_order_by(order_by)}"
    if limit is not None:
        sql += f" LIMIT {limit}"
    if offset is not None:
        sql += f" OFFSET {offset}"

    return {"sql": sql, "params": []}

# Example usage:
# query = {
#     "table": "orders",
#     "select": [
#         {"expr": "orders.id", "as": "order_id"},
#         {"expr": "COUNT(orders.items)", "as": "item_count"}
#     ],
#     "where": {
#         "AND": [
#             {"field": "orders.total", "op": ">", "value": 100},
#             {"field": "orders.status", "op": "IN", "query": {"field": "orders.id", "op": "=", "value": 1}}
#         ]
#     },
#     "having": {"op": "SUM", "field": "orders.total", "value": 1000},
#     "joins": [
#         {"type": "LEFT", "table": "items", "on": {"orders.id": "items.order_id"}}
#     ],
#     "groupBy": ["orders.status"],
#     "orderBy": [{"field": "order_id", "dir": "ASC"}],
#     "limit": 10
# }
# print(compile_query(query))
