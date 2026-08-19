export function solve(input) {
    const {
        table,
        select = ['*'],
        joins = [],
        where = {},
        groupBy = [],
        orderBy = [{ field: 'created_at', dir: 'ASC' }],
        limit = 0,
        offset = 0
    } = input.query;

    let sql = `SELECT ${select.map(c => (typeof c === 'string' ? c : `${c.expr} AS ${c.as}`)).join(', ')}`;
    let params = [];

    if (joins.length) {
        joins.forEach(j => {
            const { type, table: t, on } = j;
            const conditions = Object.entries(on).map(([leftCol, rightCol]) =>
                `${leftCol} = $${params.push(rightCol)}`
            );
            sql += ` ${type ? `${type} JOIN` : 'INNER JOIN'} ${t} ON ${conditions.join(' AND ')}`;
        });
    }

    if (where) {
        let conditions = [];
        Object.entries(where).forEach(([field, { op, value }]) => {
            if (op === 'IS NULL' || op === 'IS NOT NULL') return;
            const paramIndex = params.push(value);
            switch (op) {
                case '=':
                    conditions.push(`${field} = $${paramIndex}`);
                    break;
                case '!=':
                    conditions.push(`${field} != $${paramIndex}`);
                    break;
                case '>':
                    conditions.push(`${field} > $${paramIndex}`);
                    break;
                case '<':
                    conditions.push(`${field} < $${paramIndex}`);
                    break;
                case '>=':
                    conditions.push(`${field} >= $${paramIndex}`);
                    break;
                case '<=':
                    conditions.push(`${field} <= $${paramIndex}`);
                    break;
                case 'LIKE':
                    conditions.push(`${field} LIKE $${paramIndex}`);
                    break;
                case 'IN':
                    conditions.push(`${field} IN (${value.map(v => `$${params.push(v)}`).join(', ')})`);
                    break;
            }
        });
        sql += ` WHERE ${conditions.join(' AND ')}`;
    }

    if (groupBy.length) {
        sql += ` GROUP BY ${groupBy.map(c => c).join(',')}`;
    }

    if (orderBy.length) {
        sql += ` ORDER BY ${orderBy.map(o => `${o.field} ${o.dir || 'ASC'}`).join(', ')}`;
    }

    if (limit > 0) {
        sql += ` LIMIT ${limit}`;
    }
    if (offset > 0) {
        sql += ` OFFSET ${offset}`;
    }

    return { sql, params };
}