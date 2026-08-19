export function solve(input) {
  const { items, filter, sort, page = 1, pageSize = 10 } = input;
  
  // Filter items
  let filteredItems = [...items];
  
  if (filter) {
    const { field, op, value } = filter;
    
    filteredItems = filteredItems.filter(item => {
      const fieldValue = item[field];
      
      if (fieldValue === undefined) return false;
      
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
          return String(fieldValue).toLowerCase().includes(String(value).toLowerCase());
        default:
          return false;
      }
    });
  }
  
  // Sort items
  if (sort) {
    const { field, dir } = sort;
    const compare = (a, b) => {
      const valA = a[field];
      const valB = b[field];
      
      if (valA === undefined && valB === undefined) return 0;
      if (valA === undefined) return dir === 'asc' ? 1 : -1;
      if (valB === undefined) return dir === 'asc' ? -1 : 1;
      
      if (typeof valA === 'string' && typeof valB === 'string') {
        return dir === 'asc' 
          ? String(valA).localeCompare(String(valB)) 
          : String(valB).localeCompare(String(valA));
      } else {
        return dir === 'asc' 
          ? valA - valB 
          : valB - valA;
      }
    };
    
    filteredItems.sort((a, b) => compare(a, b));
  }
  
  // Paginate
  const startIndex = (page - 1) * pageSize;
  const endIndex = startIndex + pageSize;
  const paginatedItems = filteredItems.slice(startIndex, endIndex);
  
  const total = filteredItems.length;
  const totalPages = total === 0 ? 0 : Math.ceil(total / pageSize);
  
  return {
    items: paginatedItems,
    total,
    page,
    totalPages
  };
}