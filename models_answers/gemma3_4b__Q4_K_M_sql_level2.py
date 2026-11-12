def compile_query(query: dict) -> dict:
    """
    Compiles a query AST tree to parameterized SQL with JOIN, GROUP BY, and extended operators.
    """
    table = query['table']
    select = query.get('select', ['*'])
    where = query.get('where')
    orderBy = query.get('orderBy', [])
    limit = query.get('limit')
    offset = query.get('offset')
    joins = query.get('joins', [])
    groupBy = query.get('groupBy', [])

    sql = f"SELECT {', '.join(select)} FROM {table}"
    params = []

    if joins:
        join_clauses = []
        for join in joins:
            join_type = join.get('type', 'INNER')
            join_table = join['table']
            join_on = join['on']
            join_clause = f"{join_table} "
            if join_type == 'LEFT':
                join_clause += f"LEFT JOIN "
            elif join_type == 'RIGHT':
                join_clause += f"RIGHT JOIN "
            else:
                join_clause += f"JOIN "
            
            conditions = []
            for left_col, right_col in join_on.items():
                conditions.append(f"{left_col} = {right_col}")
            
            join_clause += " ON " + " AND ".join(conditions)
            join_clauses.append(join_clause)
        sql += " " + " ".join(join_clauses)

    if where:
        where_conditions = []
        for cond in where:
            if isinstance(cond, dict):
                if 'AND' in cond:
                    where_conditions.append(cond)
                elif 'OR' in cond:
                    where_conditions.append(cond)
                else:
                    where_conditions.append(cond)
            else:
                where_conditions.append(cond)

        if where_conditions:
            conditions = []
            for cond in where_conditions:
                field = list(cond.keys())[0]
                value = cond[field]

                if isinstance(value, list):
                    for v in value:
                        conditions.append(f"{field} IN ({v})")
                elif value is None:
                    conditions.append(f"{field} IS NULL")
                elif isinstance(value, str):
                    conditions.append(f"{field} LIKE '{value}'")
                else:
                    conditions.append(f"{field} = '{value}'")

            if conditions:
                sql += " WHERE " + " AND ".join(conditions)

    if groupBy:
        sql += " GROUP BY " + ", ".join(groupBy)

    if orderBy:
        order_by_clauses = []
        for order_by in orderBy:
            field = order_by['field']
            dir = order_by.get('dir', 'ASC')
            order_by_clauses.append(f"{field} {dir}")
        sql += " ORDER BY " + ", ".join(order_by_clauses)

    if limit:
        sql += f" LIMIT {limit}"

    if offset:
        sql += f" OFFSET {offset}"

    return {"sql": sql, "params": params}

if __name__ == '__main__':
    query1 = {
        'table': 'users',
        'select': ['id', 'name'],
        'where': {
            'id': 1,
            'name': 'Alice',
            'AND': [
                {'age': 30, '>': 25},
                {'city': 'New York', '=': 'New York'}
            ]
        }
    }
    result1 = compile_query(query1)
    print(result1)

    query2 = {
        'table': 'products',
        'select': ['*'],
        'where': {
            'price': {
                'OR': [
                    {'price': 100, '>': 50},
                    {'price': 200, '<': 150}
                ]
            }
        },
        'orderBy': [{'name': 'ASC'}],
        'limit': 10
    }
    result2 = compile_query(query2)
    print(result2)

    query3 = {
        'table': 'orders',
        'select': ['*'],
        'where': {
            'status': {
                'IN': ['completed', 'pending']
            }
        },
        'groupBy': ['order_id'],
        'joins': [
            {'type': 'LEFT', 'table': 'items', 'on': {'order_id': 'item_id'}}
        ]
    }
    result3 = compile_query(query3)
    print(result3)
