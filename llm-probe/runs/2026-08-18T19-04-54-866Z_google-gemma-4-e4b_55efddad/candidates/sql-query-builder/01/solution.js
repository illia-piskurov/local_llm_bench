export function solve(input) {
    const state = {
        sql: "",
        params: [],
        paramCount: 0,
    };

    /**
     * Handles adding a parameter value and generating the placeholder string $N.
     * @param {*} value The value to be treated as a parameter.
     * @returns {string} The SQL placeholder string ($N).
     */
    function addParam(value) {
        state.paramCount++;
        state.params.push(value);
        return `$${state.paramCount}`;
    }

    /**
     * Builds a condition for a single field comparison (base case in WHERE).
     * @param {object} condition - The condition object: { field, op, value }.
     * @returns {{sql: string, paramsUsed: number}} The SQL segment and the count of parameters added.
     */
    function buildCondition(condition) {
        let sqlPart = "";
        const { field, op, value } = condition;

        if (!field || !op) return { sql: "", paramsUsed: 0 };

        // Special handling for IS NULL / IS NOT NULL (no parameters needed)
        if (op === 'IS NULL') {
            return { sql: `${field} IS NULL`, paramsUsed: 0 };
        }
        if (op === 'IS NOT NULL') {
            return { sql: `${field} IS NOT NULL`, paramsUsed: 0 };
        }

        // Handling for IN clause (value is an array)
        if (op.toUpperCase() === 'IN' && Array.isArray(value)) {
            const placeholders = [];
            for (let i = 0; i < value.length; i++) {
                placeholders.push(addParam(value[i]));
            }
            return { sql: `${field} IN (${placeholders.join(', ')})`, paramsUsed: value.length };
        }

        // Standard parameterized comparison
        const paramPlaceholder = addParam(value);
        sqlPart = `${field} ${op} ${paramPlaceholder}`;
        return { sql: sqlPart, paramsUsed: 1 };
    }

    /**
     * Recursively processes complex logical conditions (AND/OR).
     * @param {{[key: string]: any}} conditionContainer - e.g., {"AND": [...] } or {"OR": [...]}
     * @returns {string} The combined SQL WHERE clause segment, wrapped in parentheses.
     */
    function buildLogicalCondition(conditionContainer) {
        const keys = Object.keys(conditionContainer);
        if (keys.length === 0) return "";

        const logicalOp = keys[0].toUpperCase(); // Must be AND or OR
        const conditionsArray = conditionContainer[keys[0]];

        if (!Array.isArray(conditionsArray)) {
            throw new Error("Expected array of conditions under AND/OR.");
        }

        const parts = [];
        for (const condition of conditionsArray) {
            let segment;
            if (typeof condition === 'object' && condition !== null) {
                // Base condition object
                segment = buildCondition(condition).sql;
            } else if (typeof condition === 'string') {
                // Assuming simple column string comparison, although structure implies objects/arrays.
                // If it is a simple field name used outside structured context, treat it as an error or literal.
                throw new Error("Unsupported condition format: Expected object or array.");
            } else if (Array.isArray(condition)) {
                 // Handle nested logical groups within the list itself
                 segment = buildLogicalCondition(condition).sql;
            } else {
                 throw new Error(`Unknown condition type found: ${typeof condition}`);
            }

            if (segment) {
                parts.push(segment);
            }
        }

        return `(${parts.join(` ${logicalOp} `)})`;
    }


    // --- 1. Initialization and FROM clause ---
    const query = input?.query;
    if (!query || !query.table) {
        throw new Error("Invalid input: Query must specify a table.");
    }

    state.sql += `SELECT `;
    const selectItems = query.select;

    // --- 2. SELECT clause ---
    let selectSqlParts = [];
    if (Array.isArray(selectItems)) {
        for (const item of selectItems) {
            if (typeof item === 'string') {
                selectSqlParts.push(item);
            } else if (typeof item === 'object' && item !== null && 'expr' in item && 'as' in item) {
                // Alias object: { expr: string, as: string }
                selectSqlParts.push(`${item.expr} AS ${item.as}`);
            } else {
                 throw new Error("Unsupported SELECT item format.");
            }
        }
    } else if (Array.isArray(selectItems)) {
         // Should not happen based on type checking above, but handles potential misinterpretation of structure
    } else {
        // Default to '*' if select is missing or malformed
        selectSqlParts.push('*');
    }

    state.sql += selectSqlParts.join(', ');


    // --- 3. FROM clause ---
    state.sql += ` FROM ${query.table}`;

    // --- 4. JOINs clause ---
    if (query.joins && Array.isArray(query.joins)) {
        for (const join of query.joins) {
            const type = join.type || 'INNER';
            state.sql += ` ${type} JOIN ${join.table} ON `;

            // Assuming 'on' structure is always correct mapping field names: {"left_field": "right_field"}
            const onParts = [];
            for (const leftCol in join.on) {
                if (typeof join.on[leftCol] === 'string') {
                    onParts.push(`${leftCol} = ${join.on[leftCol]}`);
                } else {
                     throw new Error("JOIN ON clause requires string comparisons.");
                }
            }
            state.sql += onParts.join(' AND ');
        }
    }

    // --- 5. WHERE clause ---
    if (query.where) {
        let whereSql = "";
        try {
             whereSql = buildLogicalCondition(query.where);
        } catch (e) {
            // If the WHERE structure is malformed, we might skip it or rethrow depending on strictness.
            console.error("Error building WHERE clause:", e.message);
            return { sql: "", params: [] }; // Return empty if critical failure in complex structure parsing
        }

        state.sql += ` WHERE ${whereSql}`;
    }

    // --- 6. GROUP BY, ORDER BY, LIMIT/OFFSET (Append logic) ---

    if (query.groupBy && Array.isArray(query.groupBy)) {
        const groupCols = query.groupBy.filter(col => typeof col === 'string');
        if (groupCols.length > 0) {
            state.sql += ` GROUP BY ${groupCols.join(', ')}`;
        }
    }

    if (query.orderBy && Array.isArray(query.orderBy)) {
        const orderParts = [];
        for (const fieldObj of query.orderBy) {
            if (!fieldObj || typeof fieldObj.field !== 'string') continue;
            
            const dir = ['DESC', 'ASC'].includes(fieldObj.dir?.toUpperCase()) ? fieldObj.dir.toUpperCase() : 'ASC';
            orderParts.push(`${fieldObj.field} ${dir}`);
        }

        if (orderParts.length > 0) {
            state.sql += ` ORDER BY ${orderParts.join(', ')}`;
        }
    }

    if (typeof query.limit === 'number' && query.limit >= 0) {
        state.sql += ` LIMIT ${query.limit}`;
    }

    if (typeof query.offset === 'number' && query.offset >= 0) {
        // If limit was set, offset usually comes after it, but we append sequentially for simplicity based on common SQL patterns.
        state.sql += ` OFFSET ${query.offset}`;
    }


    return { sql: state.sql, params: state.params };
}