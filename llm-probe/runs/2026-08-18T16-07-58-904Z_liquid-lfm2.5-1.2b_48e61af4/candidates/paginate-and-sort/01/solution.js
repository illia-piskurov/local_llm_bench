export function solve(input) {
  const { items, filter, sort, page, pageSize } = input;

  // Filtering
  let filteredItems = items.filter(item => {
    const value = filter ? filter.field === filter.value ? item[filter.field].toLowerCase() : item[filter.field];
    switch (filter.op) {
      case 'eq': return value === value;
      case 'neq': return value !== value;
      case 'gt': return item[filter.field] > value;
      case 'gte': return item[filter.field] >= value;
      case 'lte': return item[filter.field] <= value;
      case 'contains': return item[filter.field].toLowerCase().includes(value.toLowerCase());
      default: return false;
    }
  });

  // Sorting
  let sortedItems = filteredItems.sort((a, b) => {
    const comparator = sort.field === 'id' ? a.id - b.id : a[sort.field].localeCompare(b[sort.field]);
    if (comparator !== 0) return sort.dir === 'asc' ? comparator : -comparator;
    return 0;
  });

  // Pagination
  const totalItems = sortedItems.length;
  const startIndex = (page - 1) * pageSize;
  const endIndex = startIndex + pageSize;
  const paginatedItems = sortedItems.slice(startIndex, endIndex);

  const totalPages = Math.ceil(totalItems / pageSize);
  return {
    items: paginatedItems,
    total: totalItems,
    page: page,
    totalPages: totalPages
  };
}