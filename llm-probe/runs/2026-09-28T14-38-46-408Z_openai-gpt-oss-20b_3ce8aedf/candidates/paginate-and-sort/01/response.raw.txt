export function solve(input) {
  const items = input.items ? [...input.items] : [];
  let filtered = items;
  if (input.filter) {
    const { field, op, value } = input.filter;
    filtered = items.filter((item) => {
      const fieldValue = item[field];
      switch (op) {
        case 'eq':
          return fieldValue === value;
        case 'neq':
          return fieldValue !== value;
        case 'gt':
          return fieldValue > value;
        case 'gte':
          return fieldValue >= value;
        case 'lt':
          return fieldValue < value;
        case 'lte':
          return fieldValue <= value;
        case 'contains':
          if (typeof fieldValue !== 'string') return false;
          return fieldValue.toLowerCase().includes(String(value).toLowerCase());
        default:
          return false;
      }
    });
  }

  if (input.sort) {
    const { field, dir } = input.sort;
    const sorted = [...filtered];
    sorted.sort((a, b) => {
      const va = a[field];
      const vb = b[field];
      if (va < vb) return dir === 'asc' ? -1 : 1;
      if (va > vb) return dir === 'asc' ? 1 : -1;
      return 0; // stable due to array sort preserving order of equal elements
    });
    filtered = sorted;
  }

  const page = typeof input.page === 'number' && input.page > 0 ? input.page : 1;
  const pageSize = typeof input.pageSize === 'number' && input.pageSize > 0 ? input.pageSize : 10;
  const total = filtered.length;
  const totalPages = total === 0 ? 0 : Math.ceil(total / pageSize);
  const startIdx = (page - 1) * pageSize;
  const paginatedItems = filtered.slice(startIdx, startIdx + pageSize);

  return {
    items: paginatedItems,
    total,
    page,
    totalPages
  };
}