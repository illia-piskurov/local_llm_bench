export function solve(input) {
  const items = [...input.items];

  // Filter
  if (input.filter) {
    const { field, op, value } = input.filter;
    const getValue = item => String(item[field]) || '';
    const compare = val1 => Number(val1);
    const filtered = items.filter(item => {
      switch (op) {
        case 'eq':
          return compare(getValue(item)) === value;
        case 'neq':
          return compare(getValue(item)) !== value;
        case 'gt':
          return compare(getValue(item)) > value;
        case 'lt':
          return compare(getValue(item)) < value;
        case 'gte':
          return compare(getValue(item)) >= value;
        case 'lte':
          return compare(getValue(item)) <= value;
        case 'contains':
          const v = String(value).toLowerCase();
          const s = getValue(item).toLowerCase();
          return s.includes(v);
        default:
          return false;
      }
    });
    items = filtered;
  }

  // Sort (stable)
  if (input.sort) {
    const { field, dir } = input.sort;
    const sortItem = (a, b) => {
      let av = Number(a[field]) || NaN;
      let bv = Number(b[field]) || NaN;
      if (av === bv) return 0; // preserve order
      return dir === 'asc' ? av - bv : bv - av;
    };
    items = [...items].sort(sortItem);
  }

  const total = items.length;
  const page = Math.max(input.page || 1, 1);
  const size = input.pageSize || 10;
  const start = (page - 1) * size;
  const end = start + size;
  const pagedItems = items.slice(start, end);
  const totalPages = total === 0 ? 0 : Math.ceil(total / size);

  return {
    items: pagedItems,
    total,
    page,
    totalPages
  };
}