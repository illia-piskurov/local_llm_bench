export function solve(input) {
  let sql = 'SELECT *';
  if (input.query && input.query.table) {
    sql += ` FROM ${input.query.table}`;
  }

  if (input.where) {
    sql += ` WHERE ${input.where.toSql()}`;
  }

  if (input.orderBy) {
    sql += ` ORDER BY ${input.orderBy.field} $${input.orderBy.dir}`;
  }

  if (input.limit) {
    sql += ` LIMIT $${input.limit}`;
  }

  if (input.offset) {
    sql += ` OFFSET $${input.offset}`;
  }


  return { sql, params: [] };
}