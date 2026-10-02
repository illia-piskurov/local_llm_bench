export function solve(input) {
  const query = JSON.parse(JSON.stringify(input.query));
  let params = [];
  let placeholderIndex = 1;
  const nextPlaceholder = () => `$${placeholderIndex++}`;

  // SELECT clause
  let selectClause;
  if (!query.select || query.select.length === 0) {
    selectClause = '*';
  } else {
    selectClause = query.select.map(sel => {
      if (typeof sel === 'string') return sel;
      if (sel && typeof sel === 'object' && 'expr' in sel && 'as' in sel)
        return `${sel.expr} AS ${sel.as}`;
      throw new Error('Invalid select item');
    }).join(', ');
  }

  // FROM clause
  const fromClause = query.table;

  // JOIN clauses
  let joinClauses = '';
  if (Array.isArray(query.joins)) {
    joinClauses = query.joins.map(j => {
      const type = j.type ? `${j.type.toUpperCase()} ` : '';
      const onParts = Object.entries(j.on).map(
        ([leftCol, rightCol]) => `${leftCol} = ${rightCol}`
      );
      return `${type}JOIN ${j.table} ON ${onParts.join(' AND ')}`;
    }).join(' ');
  }

  // WHERE clause
  function buildCondition(cond) {
    if (cond.AND || cond.OR) {
      const key = cond.AND ? 'AND' : 'OR';
      const subconds = Array.isArray(cond[key]) ? cond[key] : [cond[key]];
      const parts = subconds.map(buildCondition);
      return `(${parts.join(` ${key} `)})`;
    }
    if (typeof cond === 'object' && cond.field && cond.op !== undefined) {
      const field = cond.field;
      const op = cond.op.toUpperCase();
      if (op === 'IS NULL' || op === 'IS NOT NULL') {
        return `${field} ${op}`;
      } else if (op === 'IN') {
        const values = Array.isArray(cond.value) ? cond.value : [];
        if (values.length === 0) {
          // Handle empty IN as false condition
          return '1=0';
        }
        const placeholders = values.map(() => nextPlaceholder());
        params.push(...values);
        return `${field} IN (${placeholders.join(', ')})`;
      } else {
        const placeholder = nextPlaceholder();
        params.push(cond.value);
        return `${field} ${op} ${placeholder}`;
      }
    }
    throw new Error('Invalid condition');
  }

  let whereClause = '';
  if (query.where) {
    const condStr = buildCondition(query.where);
    whereClause = `WHERE ${condStr}`;
  }

  // GROUP BY
  let groupByClause = '';
  if (Array.isArray(query.groupBy) && query.groupBy.length > 0) {
    groupByClause = 'GROUP BY ' + query.groupBy.join(', ');
  }

  // ORDER BY
  let orderByClause = '';
  if (Array.isArray(query.orderBy) && query.orderBy.length > 0) {
    const parts = query.orderBy.map(o => `${o.field} ${((o.dir || 'ASC').toUpperCase() === 'DESC' ? 'DESC' : 'ASC')}`);
    orderByClause = 'ORDER BY ' + parts.join(', ');
  }

  // LIMIT
  let limitClause = '';
  if (typeof query.limit === 'number' && query.limit >= 0) {
    limitClause = `LIMIT ${query.limit}`;
  }

  // OFFSET
  let offsetClause = '';
  if (typeof query.offset === 'number' && query.offset >= 0) {
    offsetClause = `OFFSET ${query.offset}`;
  }

  const sqlParts = [
    'SELECT', selectClause,
    'FROM', fromClause,
    joinClauses,
    whereClause,
    groupByClause,
    orderByClause,
    limitClause,
    offsetClause
  ].filter(Boolean).join(' ');
  return { sql: sqlParts, params };
}