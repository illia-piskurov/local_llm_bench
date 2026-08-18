export function solve(input) {
  const { items, filter, sort, page, pageSize } = input;

  // Filter logic
  let filteredItems = [...items];
  if (filter && filter.field && filter.op && filter.value) {
    const field = filter.field;
    const op = filter.op;
    const value = filter.value;
    if (op === 'eq') {
      filteredItems = items.filter(item => item[field] === value);
    } else if (op === 'neq') {
      filteredItems = items.filter(item => item[field] !== value);
    } else if (op === 'gt' || op === 'gte') {
      filteredItems = items.filter(item => 
        op === 'gt' ? item[field] > value : 
        op === 'gte' ? item[field] >= value : false
      );
    } else if (op === 'lt' || op === 'lte') {
      filteredItems = items.filter(item => 
        op === 'lt' ? item[field] < value : 
        op === 'lte' ? item[field] <= value : false
      );
    } else if (op === 'contains') {
      const lowerValue = value.toLowerCase();
      filteredItems = items.filter(item => 
        item[field].toLowerCase().includes(lowerValue)
      );
    }
  }

  // Sort logic
  let sortedItems = [...filteredItems];
  if (sort && sort.field && sort.dir) {
    const field = sort.field;
    const dir = sort.dir;
    sortedItems.sort((a, b) => {
      const valueA = a[field];
      const valueB = b[field];
      if (typeof valueA === 'string' && typeof valueB === 'string') {
        return dir === 'asc' ? valueA.localeCompare(valueB) : valueB.localeCompare(valueA);
      }
      return dir === 'asc' ? valueA - valueB : valueB - valueA;
    });
  }

  // Pagination logic
  const start = (page - 1) * pageSize;
  const end = start + pageSize;
  const paginatedItems = sortedItems.slice(start, end);

  return {
    items: paginatedItems,
    total: sortedItems.length,
    page,
    totalPages: Math.ceil(sortedItems.length / pageSize)
  };
}