def compile_query(query: dict) -> dict:
    """
    Compiles an AST-based query dictionary into a parameterized SQL string and parameter list.
    """

    class CompilerState:
        def __init__(self):
            self.params = []
            self.counter = 1

        def walk_where(self, node: dict) -> str:
            if not node:
                return ""

            # Handle logical operators (AND, OR)
            for logic_op in ("AND", "OR"):
                if logic_op in node:
                    sub_conditions = node[logic_op]
                    parts = [self.walk_where(cond) for cond in sub_conditions]
                    # Filter out empty strings from recursion
                    parts = [p for p in parts if p]
                    
                    if not parts:
                        return ""
                    
                    joined = f" {logic_op} ".join(parts)
                    # Wrap in parentheses if there are multiple conditions
                    return f"({joined})" if len(parts) > 1 else parts[0]

            # Handle leaf node (field, op, value)
            if "field" in node and "op" in node:
                field = node["field"]
                op = node["op"]
                value = node.get("value")
                
                placeholder = f"${self.counter}"
                self.params.append(value)
                self.counter += 1
                
                return f"{field} {op} {placeholder}"

            return ""

    state = CompilerState()

    # 1. SELECT and FROM
    select_cols = ", ".join(query.get("select", ["*"]))
    table_name = query["table"]
    sql_segments = [f"SELECT {select_cols} FROM {table_name}"]

    # 2. WHERE
    where_node = query.get("where")
    if where_node:
        where_clause = state.walk_where(where_node)
        if where_clause:
            sql_segments.append(f"WHERE {where_clause}")

    # 3. ORDER BY
    order_by_list = query.get("orderBy", [])
    if order_by_list:
        orders = []
        for item in order_by_list:
            direction = item.get("dir", "ASC").upper()
            orders.append(f"{item['field']} {direction}")
        sql_segments.append(f"ORDER BY {', '.join(orders)}")

    # 4. LIMIT
    if "limit" in query:
        sql_segments.append(f"LIMIT {query['limit']}")

    # 5. OFFSET
    if "offset" in query:
        sql_segments.append(f"OFFSET {query['offset']}")

    return {
        "sql": " ".join(sql_segments),
        "params": state.params
    }

# Example usage for testing:
if __name__ == "__main__":
    ast_query = {
        "table": "users",
        "select": ["id", "name", "email"],
        "where": {
            "AND": [
                {"field": "age", "op": ">=", "value": 18},
                {
                    "OR": [
                        {"field": "status", "op": "=", "value": "active"},
                        {"field": "role", "op": "=", "value": "admin"}
                    ]
                }
            ]
        },
        "orderBy": [{"field": "name", "dir": "DESC"}, {"field": "id", "dir": "ASC"}],
        "limit": 10,
        "offset": 5
    }

    result = compile_query(ast_query)
    print("SQL:", result["sql"])
    print("Params:", result["params"])
