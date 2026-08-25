export function solve(input) {
    const { items = [], filter, sort, page = 1, pageSize = 10 } = input;
    let filteredItems = [...items];

    if (filter) {
        const { field, op, value } = filter;
        const fieldValue = items[0][field] !== undefined ? items[0][field] : '';
        const caseInsensitiveValue = typeof value === 'string' ? value.toLowerCase() : value;

        filteredItems = filteredItems.filter(item => {
            const itemField = item[field];
            if (op === 'eq') return itemField === value;
            if (op === 'neq') return itemField !== value;
            if (op === 'gt') return Number(itemField) > Number(value);
            if (op === 'gte') return Number(itemField) >= Number(value);
            if (op === 'lt') return Number(itemField) < Number(value);
            if (op === 'lte') return Number(itemField) <= Number(value);
            if (op === 'contains' && typeof itemField === 'string') {
                const lowerCaseItem = itemField.toLowerCase();
                return lowerCaseItem.includes(caseInsensitiveValue);
            }
            return false;
        });
    }

    if (sort) {
        const { field, dir } = sort;
        filteredItems.sort((a, b) => {
            const aVal = a[field];
            const bVal = b[field];

            if (typeof aVal === 'string' && typeof bVal === 'string') {
                return dir === 'asc'
                    ? aVal.localeCompare(bVal)
                    : bVal.localeCompare(aVal);
            }

            const numA = Number(aVal) || 0;
            const numB = Number(bVal) || 0;

            return dir === 'asc' ? numA - numB : numB - numA;
        });
    }

    const totalItems = filteredItems.length;
    const startIndex = (page - 1) * pageSize;
    const endIndex = startIndex + pageSize;
    const paginatedItems = filteredItems.slice(startIndex, endIndex);

    return {
        items: paginatedItems,
        total: totalItems > 0 ? totalItems : 0,
        page: page,
        totalPages: Math.ceil(totalItems / pageSize) || 0
    };
}