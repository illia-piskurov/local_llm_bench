export function solve(input) {
  const { items, filter, sort, page = 1, pageSize = 10 } = input;
  let filteredItems = items;

  // Filter the items if a filter is provided
  if (filter) {
    const { field, op, value } = filter;
    filteredItems = filteredItems.filter(item => {
      switch (op) {
        case 'eq':
          return item[field] === value;
        case 'neq':
          return item[field] !== value;
        case 'gt':
          return item[field] > value;
        case 'gte':
          return item[field] >= value;
        case 'lt':
          return item[field] < value;
        case 'lte':
          return item[field] <= value;
        case 'contains':
          return String(item[field]).toLowerCase().includes(String(value).toLowerCase());
        default:
          throw new Error(`Invalid operator ${op}`);
      }
    });
  }

  // Sort the items if a sort is provided
  if (sort) {
    filteredItems.sort((a, b) => {
      const { field, dir } = sort;
      let comparison = 0;

      if (a[field] < b[field]) {
        comparison = -1;
      } else if (a[field] > b[field]) {
        comparison = 1;
      }

      return dir === 'desc' ? -comparison : comparison;
    });
  }

  // Calculate pagination
  const totalItems = filteredItems.length;
  const totalPages = Math.ceil(totalItems / pageSize);
  const startIndex = (page - 1) * pageSize;
  const endIndex = Math.min(startIndex + pageSize, totalItems);

  return {
    items: filteredItems.slice(startIndex, endIndex),
    total: totalItems,
    page,
    totalPages
  };
}