def compile_query(query):
    table = query['table']
    select = query.get('select', ['*'])
    where = query.get('where', {})
    order_by = query.get('orderBy', [{'field': '', 'dir': 'ASC'}])
    limit = query.get('limit')
    offset = query.get('offset')

    def build_select(columns):
        if columns == ['*']:
            return '*'
        return ', '.join(columns)

    def build_order_by(columns):
        order = []
        for col in columns:
            field = col['field']
            dir = col.get('dir', 'ASC')
            order.append(f'{field} {dir}')
        return ', '.join(order)

    def build_where(where):
        if isinstance(where, dict):
            if 'AND' in where:
                conditions = where['AND']
                if len(conditions) == 1:
                    return build_condition(conditions[0])
                return f'({build_condition(conditions[0])} AND {build_condition(conditions[1])})'
            elif 'OR' in where:
                conditions = where['OR']
                if len(conditions) == 1:
                    return build_condition(conditions[0])
                return f'({build_condition(conditions[0])} OR {build_condition(conditions[1])})'
            else:
                return build_condition(where)
        else:
            return build_condition(where)

    def build_condition(cond):
        field = cond['field']
        op = cond['op']
        value = cond['value']
        if op == '=':
            return f'{field} = $1'
        elif op == '!=':
            return f'{field} != $1'
        elif op == '>':
            return f'{field} > $1'
        elif op == '<':
            return f'{field} < $1'
        elif op == '>=':
            return f'{field} >= $1'
        elif op == '<=':
            return f'{field} <= $1'
        else:
            raise ValueError(f"Unsupported operator: {op}")

    params = []
    where_str = build_where(where)
    if where_str:
        where_str = f'WHERE {where_str}'
    else:
        where_str = ''
    order_by_str = build_order_by(order_by)
    if order_by_str:
        order_by_str = f'ORDER BY {order_by_str}'
    else:
        order_by_str = ''
    limit_str = ''
    if limit is not None:
        limit_str = f'LIMIT {limit}'
    offset_str = ''
    if offset is not None:
        offset_str = f'OFFSET {offset}'
    sql = f'SELECT {build_select(select)} FROM {table} {where_str} {order_by_str} {limit_str} {offset_str}'
    return {"sql": sql, "params": params}
