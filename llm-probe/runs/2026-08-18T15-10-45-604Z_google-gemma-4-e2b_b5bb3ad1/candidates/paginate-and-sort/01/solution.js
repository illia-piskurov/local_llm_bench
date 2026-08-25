export function solve(input) {
    const items = input.items || [];
    let filteredItems = [...items];

    // 1. Filtering
    if (input.filter) {
        const { field, op, value } = input.filter;
        filteredItems = filteredItems.filter(item => {
            const itemValue = item[field];

            if (itemValue === undefined || itemValue === null) {
                // Skip if the field is missing or null, depending on strictness. 
                // Assuming items must have the field for filtering unless op implies inequality checks fail.
                return false; 
            }

            switch (op) {
                case 'eq':
                    return itemValue === value;
                case 'neq':
                    return itemValue !== value;
                case 'gt':
                    return itemValue > value;
                case 'gte':
                    return itemValue >= value;
                case 'lt':
                    return itemValue < value;
                case 'lte':
                    return itemValue <= value;
                case 'contains':
                    if (typeof itemValue !== 'string' || typeof value !== 'string') {
                        return false; // Cannot perform contains on non-strings or mixed types meaningfully
                    }
                    // Case-insensitive substring matching
                    return itemValue.toLowerCase().includes(value.toLowerCase());
                default:
                    return true; // Unknown operation, keep the item (safer default)
            }
        });
    }

    // 2. Sorting
    if (input.sort) {
        const { field, dir } = input.sort;
        filteredItems.sort((a, b) => {
            const aVal = a[field];
            const bVal = b[field];

            let comparison = 0;

            // Handle numeric vs string sorting based on field type inference (simple heuristic)
            if (typeof aVal === 'number' && typeof bVal === 'number') {
                comparison = aVal - bVal;
            } else if (typeof aVal === 'string' && typeof bVal === 'string') {
                comparison = a.localeCompare(b);
            } else {
                // Fallback comparison for mixed types or non-comparable types, treating them as strings for simplicity
                const strA = String(aVal);
                const strB = String(bVal);
                comparison = strA.localeCompare(strB);
            }

            return dir === 'asc' ? comparison : -comparison;
        });
    }

    const total = filteredItems.length;
    const pageSize = input.pageSize || 10;
    const page = input.page || 1;

    // 3. Pagination
    const totalPages = Math.max(0, Math.ceil(total / pageSize));
    
    const startIndex = (page - 1) * pageSize;
    const endIndex = startIndex + pageSize;

    const paginatedItems = filteredItems.slice(startIndex, endIndex);

    return {
        items: paginatedItems,
        total: total,
        page: page,
        totalPages: totalPages
    };
}