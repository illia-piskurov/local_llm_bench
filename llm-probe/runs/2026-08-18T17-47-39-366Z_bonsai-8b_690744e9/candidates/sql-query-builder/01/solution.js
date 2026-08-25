export function solve(input) {  
  const { table, select, where, orderBy, limit, offset } = input.query;  

  let sql = `SELECT ${select.join(', ')} FROM ${table}`;  

  if (where && where.length > 0) {  
    let conditions = [];  
    let conditionStr = '';  

    for (const condition of where) {  
      if (condition.type === 'AND') {  
        conditions.push(condition);  
        conditionStr += ` AND `;  
      } else if (condition.type === 'OR') {  
        conditions.push(condition);  
        conditionStr += ` OR `;  
      } else {  
        const [field, op, value] = Object.entries(condition);  
        conditionStr += `${field} ${op} ${value ? '' : 'IS NULL'}`;  
      }  

      conditions[conditions.length - 1].value = value ? value : '';  
    }  

    sql += ` WHERE ${conditionStr}`;  
  }  

  if (orderBy) {  
    const orderConditions = [];  
    let conditionStr = '';  

    for (const condition of orderBy) {  
      const [field, dir] = Object.entries(condition);  
      orderConditions.push(`${field} ${dir}`);  
      conditionStr += ` ORDER BY ${conditionStr ? ' AND ' : ''}${field}`;  
    }  

    sql += ` ORDER BY ${conditionStr}`;  
  }  

  if (limit) {  
    sql += ` LIMIT ${limit}`;  
  }  

  if (offset) {  
    sql += ` OFFSET ${offset}`;  
  }  

  let params = [];  

  select.forEach((col, index) => {  
    if (typeof col === 'object' && col.as !== undefined) {  
      params.push(col.as);  
    } else {  
      params.push(col);  
    }  
  });  

  // Handle IN condition  
  where?.forEach(condition => {  
    if (condition.type === 'IN') {  
      const [field, value] = Object.entries(condition);  
      const array = value ? JSON.stringify(value) : '';  
      sql += `${field} IN (${array})`;  
    }  
  });  

  return { sql, params };  
}