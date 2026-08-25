export function solve(input) {
  const { table, select, where, orderBy, limit, offset } = input.query;
  const params = [];
  let sqlParts = [];

  // Build SELECT part
  if (select.length > 0) {
    sqlParts.push(`SELECT ${select.join(', ')}`);
  }
  if (where) {
    const whereParts = [];
    for (const condition of where) {
      const [field, op, value] = condition;
      let param = '';
      if (op === 'IS NULL' || op === 'IS NOT NULL') param += field;
      else if (op === 'IN') {
        param = `${field} IN (${value.join(',')})`;
      } else {
        param += `$${value}`;
      }
      whereParts.push(`WHERE ${field} ${op} ${param}`);
    }
    sqlParts.push(`WHERE ${whereParts.join(' AND ')}`);
  }

  // Handle joins
  if (where?.type && where.type === 'INNER') {
    const joinParts = [];
    for (const { table: joinTable, on } of where) {
      joinParts.push(`JOIN ${joinTable} ON ${on[leftCol]} = ${on[rightCol]}`);
    }
    sqlParts.push(`JOIN ${table} ON ${joinParts.join(' ')}`);
  }

  // Build WHERE clause
  const whereClause = where ? `WHERE ${where}` : '';
  sqlParts.push(whereClause);

  // GroupBy and orderBy handling (simplified)
  const groupBy = where?.groupBy || [];
  const orderBy = where?.orderBy || [];
  const paramsLength = Math.min(limit ? parseInt(limit) : 0, params.length);
  const orderedParams = params.slice(0, paramsLength).map((_, i) => `$${i + 1}`);

  if (orderBy) {
    sqlParts.push(`ORDER BY ${orderBy[0].field} ${orderBy.dir ? ' ASC' : ' DESC'}`);
    params.push(orderedParams);
  }

  // Compose final SQL
  const sql = sqlParts.join('');
  return { sql, params: params };
}