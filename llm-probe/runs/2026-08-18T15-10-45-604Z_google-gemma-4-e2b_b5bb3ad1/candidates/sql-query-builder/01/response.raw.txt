export function solve(input) {
    const query = input.query || {};

    let sqlParts = [];
    let params = [];
    let paramCounter = 1;

    // --- 1. SELECT Clause ---
    let selectClause = [];
    if (query.select && Array.isArray(query.select)) {
        if (query.select.length === 0) {
            selectClause.push('*');
        } else {
            selectClause = query.select;
        }
    }
    
    // Handle select aliases/expressions if necessary (simplified: assume direct columns for now based on example structure)
    for (const item of selectClause) {
        sqlParts.push(item);
    }

    // --- 2. FROM Clause ---
    if (query.table) {
        sqlParts.push(`FROM ${query.table}`);
    } else {
        // Default handling if table is missing, though input implies it exists
        sqlParts.push(`FROM *`); 
    }

    // --- 3. JOIN Clauses ---
    if (query.joins && Array.isArray(query.joins)) {
        for (const join of query.joins) {
            const type = join.type ? join.type.toUpperCase() : 'INNER';
            const joinSql = `JOIN ${type} ${join.table} ON ${Object.entries(join.on).map(([l, r]) => `${l} = ${r}`).join(' AND ')}`;
            sqlParts.push(joinSql);
        }
    }

    // --- 4. WHERE Clause (Recursive Parameter Handling) ---
    if (query.where) {
        const whereConditions = query.where;

        /**
         * Recursively processes a condition structure and builds SQL fragments and parameters.
         * It uses an internal counter for parameter indexing.
         * @param {object} conditions - The current level of AND/OR structure.
         * @param {number} index - The starting parameter index for this block.
         * @returns {{sql: string, params: any[], nextIndex: number}}
         */
        function processWhere(conditions, index) {
            let currentSqlParts = [];
            let currentParams = [];
            let nextIndex = index;

            for (const conditionGroup of conditions) {
                if (conditionGroup.AND) {
                    // Handle AND block
                    const andResults = processWhere(conditionGroup.AND, nextIndex);
                    currentSqlParts.push(`(${andResults.sql})`);
                    currentParams.push(...andResults.params);
                    nextIndex = andResults.nextIndex;
                } else if (conditionGroup.OR) {
                    // Handle OR block
                    const orResults = processWhere(conditionGroup.OR, nextIndex);
                    currentSqlParts.push(`(${orResults.sql})`);
                    currentParams.push(...orResults.params);
                    nextIndex = orResults.nextIndex;
                } else {
                    // Base case: Single condition check
                    const field = conditionGroup.field;
                    const op = conditionGroup.op;
                    const value = conditionGroup.value;
                    let paramSql = '';
                    let newParams = [];

                    if (['IS NULL', 'IS NOT NULL'].includes(op)) {
                        // No parameters needed for IS NULL/IS NOT NULL
                        paramSql = `${field} ${op}`;
                    } else if (op === 'IN' && Array.isArray(value)) {
                        // Handle IN operator: field IN ($n, $n+1, ...)
                        const placeholders = value.map((_, i) => `$${nextIndex + i}`);
                        paramSql = `${field} IN (${placeholders.join(', ')})`;
                        newParams = value;
                        nextIndex += value.length;
                    } else {
                        // Standard comparison operators: field OP $n
                        paramSql = `${field} ${op} $${nextIndex}`;
                        newParams = [value];
                        nextIndex += 1;
                    }

                    currentSqlParts.push(paramSql);
                    currentParams.push(...newParams);
                    nextIndex = nextIndex; // index is already handled by paramCounter logic flow below, but we track it here.
                }
            }
            return { sql: currentSqlParts.join(' AND '), params: currentParams, nextIndex: nextIndex };
        }

        // Start processing the top level of WHERE clauses
        const whereResult = processWhere(whereConditions, paramCounter);
        sqlParts.push(`WHERE ${whereResult.sql}`);
        params.push(...whereResult.params);
        paramCounter += whereResult.nextIndex;
    }

    // --- 5. GROUP BY Clause ---
    if (query.groupBy && Array.isArray(query.groupBy)) {
        sqlParts.push(`GROUP BY ${query.groupBy.join(', ')}`);
    }

    // --- 6. ORDER BY Clause ---
    if (query.orderBy && Array.isArray(query.orderBy)) {
        const orderByClauses = query.orderBy.map(sort => {
            let dir = sort.dir ? sort.dir.toUpperCase() : 'ASC';
            return `${sort.field} ${dir}`;
        });
        sqlParts.push(`ORDER BY ${orderByClauses.join(', ')}`);
    }

    // --- 7. LIMIT and OFFSET ---
    if (typeof query.limit === 'number') {
        sqlParts.push(`LIMIT ${query.limit}`);
    }
    if (typeof query.offset === 'number') {
        sqlParts.push(`OFFSET ${query.offset}`);
    }

    const sql = sqlParts.join(' ');

    return {
        sql: sql.trim(),
        params: params
    };
}