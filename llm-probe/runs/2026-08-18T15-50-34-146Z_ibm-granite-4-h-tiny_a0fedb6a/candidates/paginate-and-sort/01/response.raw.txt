export function solve(input) {
  const items = input.items;
  const filter = input.filter;
  const sort = input.sort;
  const page = input.page || 1;
  const pageSize = input.pageSize || 10;

  let filteredItems = [...items];
  if (filter) {
    const { field, op, value } = filter;
    switch (op) {
      case 'eq':
        filteredItems = filteredItems.filter(item => item[field] === value);
        break;
      case 'neq':
        filteredItems = filteredItems.filter(item => item[field] !== value);
        break;
      case 'gt':
        filteredItems = filteredItems.filter(item => item[field] > value);
        break;
      case 'gte':
        filteredItems = filteredItems.filter(item => item[field] >= value);
        break;
      case 'lt':
        filteredItems = filteredItems.filter(item => item[field] < value);
        break;
      case 'lte':
        filteredItems = filteredItems.filter(item => item[field] <= value);
        break;
      case 'contains':
        filteredItems = filteredItems.filter(
          item =>
            String(item[field]).toLowerCase().includes(String(value).toLowerCase())
        );
        break;
    }
  }

  let sortedItems = [...filteredItems];
  if (sort) {
    const { field, dir } = sort;
    const reverse = dir === 'desc';
    sortedItems.sort((a, b) => {
      const valueA = a[field];
      const valueB = b[field];
      return reverse ? compare(valueB, valueA) : compare(valueA, valueB);
    });
  }

  const total = sortedItems.length;
  const totalPages = Math.ceil(total / pageSize);

  const startIndex = (page - 1) * pageSize;
  const endIndex = Math.min(startIndex + pageSize, total);
  const paginatedItems = sortedItems.slice(startIndex, endIndex);

  return {
    items: paginatedItems,
    total,
    page,
    totalPages
  };
}

function compare(a, b) {
  if (a < b) return -1;
  if (a > b) return 1;
  return 0;
}