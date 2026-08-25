def compile_query(query: dict) -> dict:
    def build_condition(condition):
        if isinstance(condition, dict):
            op = list(condition.keys())[0]
            values = condition[op]
            if op in ['AND', 'OR']:
                sub_conditions = [build_condition(c) for c in values]
                return f"({') {op.upper()} ('.join(sub_conditions)})" if len(values) > 1 else sub_conditions[0]
            elif op == 'NOT':
                return f"NOT ({build_condition(values)})" if len(values) == 1 else "NOT ({})".format(
                    build_condition(values[0]))
            else:
                field, value = list(condition.items())[0]
                params.append(value)
                return f"{field} = ${{len(params)}}"
        elif isinstance(condition, list):
            return ' AND '.join(build_condition(c) for c in condition)
        else:
            raise ValueError("Unsupported condition type")

    def build_select(columns):
        if not columns:
            return "*"
        return ", ".join(columns)

    def build_order_by(order_by):
        if not order_by:
            return ""
        return " ORDER BY " + ", ".join(f"{field} {'ASC' if 'dir' not in o else o['dir']}" for field, o in order_by)

    def build_limit_offset(limit, offset):
        limit_clause = f" LIMIT {limit}" if limit is not None else ""
        offset_clause = f" OFFSET {offset}" if offset is not None else ""
        return limit_clause + offset_clause

    params = []
    sql_parts = []

    table = query.get('table')
    select = query.get('select', ['*'])
    where = query.get('where')
    order_by = query.get('orderBy', [])
    limit = query.get('limit')
    offset = query.get('offset')

    sql_parts.append(f"SELECT {build_select(select)} FROM {table}")
    if where:
        sql_parts.append("WHERE " + build_condition(where))
    sql_parts.extend(build_order_by(order_by))
    sql_parts.append(build_limit_offset(limit, offset))

    return {"sql": ' '.join(sql_parts), "params": params}
