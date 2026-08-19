export function solve(input) {
  let filtered = input.items;
  if (input.filter) {
    const { field, op, value } = input.filter;
    filtered = input.items.filter(item => {
      const fieldValue = String(item[field]);
      switch (op) {
        case 'contains':
          return fieldValue.toLowerCase().includes(value.toLowerCase());
        default:
          return (
            (op === 'eq' && fieldValue === value) ||
            (op === 'neq' && fieldValue !== value) ||
            (op === 'gt' && fieldValue > value) ||
            (op === 'gte' && fieldValue >= value) ||
            (op === 'lt' && fieldValue < value) ||
            (op === 'lte' && fieldValue <= value)
          );
      }
    });
  }

  if (input.sort) {
    const { field, dir } = input.sort;
    filtered.sort((a, b) => {
      const valA = String(a[field]);
      const valB = String(b[field]);
      if (dir === 'asc') {
        return valA.localeCompare(valB);
      }
      return valB.localeCompare(valA);
    });
  }

  const page = input.page || 1;
  const pageSize = input.pageSize || 10;

  const start = (page - 1) * pageSize;
  const end = start + pageSize;
  const paginated = filtered.slice(start, end);

  const total = filtered.length;
  const totalPages = total === 0 ? 0 : Math.ceil(total / pageSize);

  return {
    items: paginated,
    total,
    page,
    totalPages
  };
}