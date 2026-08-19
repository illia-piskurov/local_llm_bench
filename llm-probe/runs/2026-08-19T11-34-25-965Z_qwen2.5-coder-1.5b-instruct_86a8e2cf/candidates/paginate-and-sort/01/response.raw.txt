export function solve(input) {
  const filter = input.filter || {};
  const sort = input.sort || {};
  const page = input.page || 1;
  const pageSize = input.pageSize || 10;

  let items = input.items.slice();

  if (filter.field && filter.op) {
    switch (filter.op.toLowerCase()) {
      case 'eq':
        items = items.filter(item => item[filter.field] === filter.value);
        break;
      case 'neq':
        items = items.filter(item => item[filter.field] !== filter.value);
        break;
      case 'gt':
        items = items.filter(item => item[filter.field] > filter.value);
        break;
      case 'gte':
        items = items.filter(item => item[filter.field] >= filter.value);
        break;
      case 'lt':
        items = items.filter(item => item[filter.field] < filter.value);
        break;
      case 'lte':
        items = items.filter(item => item[filter.field] <= filter.value);
        break;
      case 'contains':
        const regex = new RegExp(filter.value, 'i');
        items = items.filter(item => regex.test(item[filter.field]));
        break;
    }
  }

  if (sort.field && sort.dir) {
    items.sort((a, b) => {
      if (sort.dir === 'asc') {
        return a[sort.field] - b[sort.field];
      } else {
        return b[sort.field] - a[sort.field];
      }
    });
  }

  const total = items.length;
  const totalPages = Math.ceil(total / pageSize);

  return { items, total, page, totalPages };
}