def compile_query(query: dict) -> dict:
    params = []
    param_counter = [0]  # Используем список, чтобы счетчик был доступен в вложенной функции

    def process_where(cond):
        # Базовый случай: простое условие
        if 'field' in cond:
            field = cond['field']
            op = cond['op']
            val = cond['value']

            # IS NULL / IS NOT NULL
            if op in ('IS NULL', 'IS NOT NULL'):
                return f"{field} {op} NULL", param_counter[0]

            # IN (список значений)
            elif op == 'IN':
                placeholders = []
                for v in val:
                    params.append(v)
                    placeholders.append(f"${param_counter[0]}")
                    param_counter[0] += 1
                return f"{field} IN ({', '.join(placeholders)})", param_counter[0]

            # LIKE
            elif op == 'LIKE':
                params.append(val)
                placeholder = f"${param_counter[0]}"
                param_counter[0] += 1
                return f"{field} {op} {placeholder}", param_counter[0]

            # Стандартные операторы
            else:
                params.append(val)
                placeholder = f"${param_counter[0]}"
                param_counter[0] += 1
                return f"{field} {op} {placeholder}", param_counter[0]

        # Логическое И (AND)
        elif 'AND' in cond:
            sub_conds = cond['AND']
            parts = []
            for sub in sub_conds:
                sql_part, idx = process_where(sub)
                parts.append(sql_part)
                param_counter[0] = idx
            # Оборачиваем в скобки, если условий больше одного
            if len(sub_conds) > 1:
                return f"({' AND '.join(parts)})", param_counter[0]
            else:
                return parts[0], param_counter[0]

        # Логическое ИЛИ (OR)
        elif 'OR' in cond:
            sub_conds = cond['OR']
            parts = []
            for sub in sub_conds:
                sql_part, idx = process_where(sub)
                parts.append(sql_part)
                param_counter[0] = idx
            # Оборачиваем в скобки, если условий больше одного
            if len(sub_conds) > 1:
                return f"({' OR '.join(parts)})", param_counter[0]
            else:
                return parts[0], param_counter[0]

    # Формирование SQL частей
    parts = []

    # SELECT
    select_list = query.get('select', ['*'])
    if select_list == ['*']:
        parts.append("SELECT *")
    else:
        parts.append(f"SELECT {', '.join(select_list)}")

    # FROM
    parts.append(f"FROM {query['table']}")

    # JOINS
    if 'joins' in query:
        for join in query['joins']:
            join_type = join.get('type', 'INNER')
            on_conditions = []
            for left_col, right_col in join['on'].items():
                on_conditions.append(f"{left_col} = {right_col}")
            parts.append(f"{join_type} JOIN {join['table']} ON {' AND '.join(on_conditions)}")

    # WHERE
    if 'where' in query:
        where_sql, _ = process_where(query['where'])
        parts.append(f"WHERE {where_sql}")

    # GROUP BY
    if 'groupBy' in query:
        parts.append(f"GROUP BY {', '.join(query['groupBy'])}")

    # ORDER BY
    if 'orderBy' in query:
        order_parts = []
        for item in query['orderBy']:
            field = item['field']
            direction = item.get('dir', 'ASC')
            order_parts.append(f"{field} {direction}")
        parts.append(f"ORDER BY {', '.join(order_parts)}")

    # LIMIT
    if 'limit' in query:
        parts.append(f"LIMIT {query['limit']}")

    # OFFSET
    if 'offset' in query:
        parts.append(f"OFFSET {query['offset']}")

    sql = " ".join(parts)

    return {"sql": sql, "params": params}
